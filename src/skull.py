"""
This module provides an software to skull stripping of a given modality.

Usage:
    Initialize an instance.
    e.g:
        skull_stripper = SkullStripper()

    Run skull stripping method:
    e.g:
        mask_path = skull.stripper.strip_skull(input_path, output_path, want_tissues)
"""
from __future__ import division
import subprocess
import shlex
import os
import numpy as np
import nibabel as nib
from nilearn.image import math_img
from . import helpers as utils
from . import registration as reg


class SkullStripper():

    # Intialize the skull stripper class
    # @param input_path : Path to the input modality to skull strip
    # @param output_path : Path the to output folder.
    # @param want_tissue: Boolean for outputting the tissue registrations
    def __init__(self, input_path, output_path, want_tissues, want_atlas):

        self.input_path = input_path
        self.output_path = output_path
        self.want_tissues = want_tissues
        self.want_atlas = want_atlas

        self.name = os.path.splitext(os.path.splitext(os.path.basename(input_path))[0])[0]
        self.atlas = utils.get_relative_path("Atlas")
        self.ss_sh_path = utils.get_relative_path(os.path.join("sh", "skull_strip.sh"))

    # Deformable registration of the stripped atlas to the anatomy using NiftyReg
    # @param atlas_path : path to the skull stripped atlas
    # @param anatomy_path : path to the stripped modality
    def deformable_registration(self, atlas_path, anatomy_path):
        print("\n Deformable tissue registration started \n -----------------")
        aff_reg = utils.get_relative_path('t1_atlas_aff_reg.nii.gz')
        aff_trans = utils.get_relative_path('t1_atlas_aff_transformation.txt')
        f3d_cpp = utils.get_relative_path('t1_atlas_f3d_cpp.nii.gz')
        f3d_reg = utils.get_relative_path(self.name + '_atlas_reg_deform.nii.gz')
        tissue_reg = utils.get_relative_path(os.path.join(self.output_path, self.name))
        tissueAtlas = utils.get_relative_path(os.path.join(self.output_path, self.name + '_'))

        reg.niftireg_affine_registration(atlas_path, anatomy_path, transform_path=aff_trans, result_path=aff_reg)
        reg.niftireg_nonrigid_registration(atlas_path, anatomy_path, transform_path=aff_trans, cpp_path=f3d_cpp,
                                           result_path=f3d_reg)

        # Apply tranfromaton to the brain tissue
        for tissue in ["csf", "gm", "wm"]:
            reg.niftireg_transform(tissueAtlas + tissue + ".nii.gz", anatomy_path, f3d_cpp,
                                   result_path=tissue_reg + "_" + tissue + "temp.nii.gz", cpp=True)
            img = nib.load(tissue_reg + "_" + tissue + "temp.nii.gz")
            mask = math_img('(img - np.min(img))/(np.max(img)-np.min(img))', img=img)
            nib.save(mask, tissue_reg + "_" + tissue + "temp.nii.gz")
            os.remove(tissueAtlas + tissue + ".nii.gz")
            os.rename(tissueAtlas + tissue + "temp.nii.gz", tissueAtlas + tissue + ".nii.gz")
            print("%s image is saved to: %s" % (tissue, tissueAtlas + tissue + ".nii.gz"))

        # Apply transformation to brain mask
        basicMaskPath = os.path.join(self.output_path, self.name + "_mask.nii.gz")
        refinedMaskPath = os.path.join(self.output_path, self.name + "_mask_refined_reg.nii.gz")
        reg.niftireg_transform(basicMaskPath, anatomy_path, f3d_cpp, result_path=refinedMaskPath, cpp=True)

        os.remove(aff_reg)
        os.remove(aff_trans)
        os.remove(f3d_cpp)

        if self.want_atlas:
            regAtlasPath = os.path.join(self.output_path, self.name + "_atlas_reg_deform.nii.gz")
            os.rename(f3d_reg, regAtlasPath)
        else:
            os.remove(f3d_reg)

    # Apply a mask to the modality
    # @param anatomy_path : Path to the input modality
    # @param mask_path : Path to the brain mask
    # @param output_name: output name of the stripped modality
    def apply_mask(self, image_path, mask_path, output_name):
        mask = nib.load(os.path.join(self.output_path, mask_path))
        patient = nib.load(image_path)

        # Reshape (in some cases data resolution is (x,y,z,1), reshape removes the 4th dimension
        tmp1 = patient.get_data()
        res = tmp1.shape
        tmp2 = tmp1.reshape(res[0], res[1], res[2])

        masked_data = np.multiply(tmp2, mask.get_data())
        # masked_data = np.multiply(patient.get_data(), mask.get_data())
        masked_data = nib.Nifti1Image(masked_data, patient.affine, patient.header)
        path_to_save = utils.get_relative_path(os.path.join(self.output_path, output_name + ".nii.gz"))
        nib.save(masked_data, path_to_save)
        return path_to_save

    def strip_skull(self):

        """ Perform skull stripping"""
        print("Skull stripping started. \n --------------------------- \n")
        print("Input Modality: %s \n" % self.input_path)
        print("Output Folder : %s \n" % self.output_path)

        # 1) Rigid registration of Atlas to Patient -> basic mask + tissue approximations
        print("\nCompute basic mask: \n -----------------")
        moving_image = self.atlas
        fixed_image = self.input_path
        command = shlex.split(
            "%s %s %s %s %s" % (self.ss_sh_path, fixed_image, moving_image, self.output_path, self.name))
        stripping = subprocess.call(command)

        # make the mask binary
        atlas_reg_path = os.path.join(self.output_path, self.name + "_atlas_reg.nii")
        basic_mask_path = os.path.join(self.output_path, self.name + "_mask.nii.gz")
        mask = nib.load(os.path.join(basic_mask_path))
        mask = math_img('img > 0.9', img=mask)
        nib.save(mask, basic_mask_path)

        # 2) deformable registration between skull stripper atlas and skull strip patient (use the basic mask)
        # stripping = subprocess.call(command)
        stripped_atlas = self.apply_mask(atlas_reg_path, self.name + "_mask.nii.gz", "masked_atlas")
        stripped_image = self.apply_mask(fixed_image, self.name + "_mask.nii.gz", self.name + "_masked_basic")
        self.deformable_registration(stripped_atlas, stripped_image)

        # rename the first mask
        os.rename(basic_mask_path, os.path.join(self.output_path, self.name + "_mask_basic.nii.gz"))

        # 3) Compute new mask from the tissue approximations
        print("\nComputing refined mask \n -------------")
        wm_path = os.path.join(self.output_path, self.name + "_wm.nii.gz")
        gm_path = os.path.join(self.output_path, self.name + "_gm.nii.gz")
        csf_path = os.path.join(self.output_path, self.name + "_csf.nii.gz")
        basic_mask_path = os.path.join(self.output_path, self.name + "_mask_basic.nii.gz")

        wm = nib.load(wm_path)
        gm = nib.load(gm_path)
        csf = nib.load(csf_path)
        basic_mask = nib.load(basic_mask_path)

        # soft mask + remove background
        soft_mask = np.add(wm.get_data(), gm.get_data())
        soft_mask = np.add(soft_mask, csf.get_data())
        soft_mask = np.multiply(soft_mask, basic_mask.get_data())

        # background = np.min(soft_mask)
        # soft_mask[ soft_mask <= 2* background] = 0

        soft_mask = nib.Nifti1Image(soft_mask, wm.affine, wm.header)
        path_to_save = utils.get_relative_path(os.path.join(self.output_path, self.name + "_mask_soft.nii.gz"))
        nib.save(soft_mask, path_to_save)

        # cut outliers from the soft mask
        data = np.reshape(soft_mask.get_data(), (1, np.product(soft_mask.get_data().shape)))
        dataNN = data[data != 0]
        m = np.mean(dataNN)
        s = np.std(dataNN)
        LB = m - 3.0 * s
        refined_mask = soft_mask.get_data()
        refined_mask[refined_mask < LB] = 0
        refined_mask[refined_mask >= LB] = 1
        refined_mask = nib.Nifti1Image(refined_mask, wm.affine, wm.header)
        path_to_save_mask = utils.get_relative_path(os.path.join(self.output_path, self.name + "_mask.nii.gz"))
        nib.save(refined_mask, path_to_save_mask)

        # 4) Apply the refine mask to image and to modalities
        print("Applying refined mask \n")
        stripped_image = self.apply_mask(fixed_image, self.name + "_mask.nii.gz", self.name + "_masked")
        print("Results save as %s \n" % stripped_image)

        if not self.want_tissues:
            os.remove(wm_path)
            os.remove(gm_path)
            os.remove(csf_path)

        # Clean up
        os.remove(stripped_atlas)
        os.remove(os.path.join(self.output_path, self.name + "_atlas_reg.nii"))
        os.remove(os.path.join(self.output_path, self.name + "_atlas_reg.nii0GenericAffine.mat"))

        print('---------------------------\nSkull Stripping Finished.')
