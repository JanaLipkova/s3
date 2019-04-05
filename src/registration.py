"""
Created on Apr 24, 2015

@author: Esther Alberts
"""

import os
from . import paths


def niftireg_affine_registration(moving_path,
                                 fixed_path,
                                 transform_path=None,
                                 result_path=None,
                                 rigid_only=False):
    """ Perform an affine registration.
    
    Parameters
    ----------
    moving_path : str
        .nii or .nii.gz path to the moving image
    fixed_path : str
        .nii or .nii.gz path to the reference image
    transform_path : str
        result path to the affine transformation matrix (.txt)
    result_path : str
        .nii or .nii.gz path to the resultant image
    """

    _check_overwrite_issue(moving_path, result_path)
    _check_existant(moving_path, fixed_path)
    if result_path is None:
        result_path = paths.get_reg_path(moving_path)
    if transform_path is None:
        transform_path = paths.get_transform_path(moving_path)

    # Register to reference file
    cmd = 'reg_aladin'
    cmd += ' -flo ' + moving_path
    cmd += ' -ref ' + fixed_path
    cmd += ' -aff ' + transform_path
    cmd += ' -res ' + result_path
    if rigid_only:
        cmd += ' -rigOnly'
    ans = os.system(cmd + ' > /dev/null')
    if ans != 0:
        cmd = paths.registration_dir + cmd
        ans = os.system(cmd + ' > /dev/null')
        if ans != 0:
            err = 'Niftireg binary not found'
            raise RuntimeError(err)


def niftireg_nonrigid_registration(moving_path,
                                   fixed_path,
                                   transform_path=None,
                                   cpp_path=None,
                                   result_path=None):
    """ Perform a (fast free-form deformation) non-rigid registration.
    
    Parameters
    ----------
    moving_path : str
        .nii or .nii.gz path to the moving image
    fixed_path : str
        .nii or .nii.gz path to the reference image
    transform_path : str
        path to an input affine transformation matrix (.txt)
    cpp_path : str
        result path to a control point grid image (.nii, .nii.gz)
    result_path : str
        .nii or .nii.gz path to the resultant image
    """

    _check_overwrite_issue(moving_path, result_path)
    if result_path is None:
        result_path = paths.get_reg_path(moving_path)

    # Register to reference file

    cmd = 'reg_f3d '
    cmd += '-flo ' + moving_path + ' '
    cmd += '-ref ' + fixed_path + ' '
    if transform_path is not None:
        cmd += '-aff ' + transform_path + ' '
    cmd += '-res ' + result_path + ' '
    if cpp_path is not None:
        cmd += '-cpp ' + cpp_path + ' '
    ans = os.system(cmd + ' > /dev/null')
    if ans != 0:
        cmd = paths.registration_dir + cmd
        ans = os.system(cmd + ' > /dev/null')
        if ans != 0:
            err = 'Niftireg binary not found'
            raise RuntimeError(err)


def niftireg_transform(moving_path,
                       fixed_path,
                       transform_path,
                       result_path=None,
                       cpp=False):
    """ Transform a moving image to a reference image using a 
    transformation previously calculated.
    
    Parameters
    ----------
    moving_path : str
        .nii or .nii.gz path to the moving image
    fixed_path : str
        .nii or .nii.gz path to the reference image
    transform_path : str
        if not cpp: path to an affine transformation matrix (.txt),
        else: path to a control point grid image (.nii, .nii.gz)
    result_path : str
        .nii or .nii.gz path to the resultant image
    cpp : bool
        If cpp, transform_path points to a control point grid, 
        if not cpp, transform_path point to an affine transformation 
        matrix.
    """

    _check_overwrite_issue(moving_path,
                           result_path)
    if result_path is None:
        result_path = paths.get_reg_path(moving_path)

    # Register to reference file
    cmd = 'reg_resample '
    cmd += '-flo ' + moving_path + ' '
    cmd += '-ref ' + fixed_path + ' '
    if not cpp:
        cmd += '-aff ' + transform_path + ' '
    else:
        cmd += '-cpp ' + transform_path + ' '
    cmd += '-res ' + result_path + ' '

    ans = os.system(cmd + ' > /dev/null')
    if ans != 0:
        cmd = paths.registration_dir + cmd
        ans = os.system(cmd + ' > /dev/null')
        if ans != 0:
            err = 'Niftireg binary not found'
            raise RuntimeError(err)


def _check_overwrite_issue(moving_path, result_path):
    """ Throw an error if the moving path and the result path are identical. """

    if moving_path == result_path:
        raise RuntimeError('You cannot overwrite original files, ' + \
                           'chose appropriate save paths')


def _check_existant(*args):
    """ Throw an error if any of the paths doesnt exist. """

    for path in args:
        if not os.path.exists(path):
            err = path[-50:] + ' doesnt exist'
            raise ValueError(err)
