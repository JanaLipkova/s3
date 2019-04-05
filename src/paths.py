"""
Created on Jan 18, 2018

@author: Esther Alberts
"""

import os

########################################################################
# Functions giving names to store registration results ####

GM = 0
WM = 1
CSF = 2
TISSUES = ['gm', 'wm', 'csf']
gm = TISSUES[GM]
wm = TISSUES[WM]
csf = TISSUES[CSF]

# paths
registration_dir = '/usr/local/lib/nifty_reg-1.3.9/nifty_reg/build/reg-apps/'
atlas_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                         'atlas_sri24_spm8')

# atlas paths
ATLAS_SPM = {}
# add atlas tissues
atlas_spm_tissues = os.path.join(atlas_dir, 'apriori')
for tissue in TISSUES:
    ATLAS_SPM[tissue] = {}
    ATLAS_SPM[tissue]['high_uint8'] = \
        os.path.join(atlas_spm_tissues, '%s_high.nii.gz' % tissue)
# add atlas modalities
atlas_spm_mod = os.path.join(atlas_dir, 'templates')
ATLAS_SPM['t1'] = os.path.join(atlas_spm_mod, 'T1.gz.nii')
ATLAS_SPM['t1_masked'] = os.path.join(atlas_spm_mod, 'T1_brain.nii.gz')
ATLAS_SPM['t2'] = os.path.join(atlas_spm_mod, 'T2.gz.nii')
ATLAS_SPM['t2_masked'] = os.path.join(atlas_spm_mod, 'T2_brain.nii.gz')
ATLAS_SPM['pd'] = os.path.join(atlas_spm_mod, 'PD.gz.nii')
ATLAS_SPM['pd_masked'] = os.path.join(atlas_spm_mod, 'PD_brain.nii.gz')

# example path
T1_EXAMPLE = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                          'example',
                          'brats2016_test_tcia_pat114_0087',
                          't1.nii.gz')


########################################################################

def get_reg_dir(save_dir):
    return os.path.join(save_dir, 'registered_tissues')


def get_reg_tissue_paths(save_dir, exist=True):
    """ Get paths to brain tissue segmentations coming from brain tissue
    atlas maps registered to this patient.

    If exist, the tissue paths should exist or an error is thrown.

    """

    reg_tissues = {}
    all_exist = True
    for tissue in TISSUES:
        new_dir = get_reg_dir(save_dir)
        make_dir(new_dir)
        this_path = os.path.join(new_dir, tissue + '_atlas_reg.nii.gz')
        reg_tissues[tissue] = this_path

        all_exist = all_exist and os.path.exists(reg_tissues[tissue])

    if not all_exist and exist:
        err = 'Registered tissue paths not found, ' + \
              'they dont exist for ' + save_dir
        raise RuntimeError(err)

    return reg_tissues


def get_reg_path(path, present=False):
    path = in_dirname(path, 'registration')
    path = get_path(path,
                    suffix='reg',
                    present=present)

    return path


def get_transform_path(path, present=False):
    path = in_dirname(path, 'registration')
    path = get_path(path,
                    suffix='aff_matrix',
                    present=present)
    path = set_extension(path, extension='txt')

    return path


def get_path(path, suffix='', present=False):
    path = extend_basename(path, suffix)
    if (not os.path.isfile(path)) and present:
        raise IOError('File ' + path + 'does not exist')
    return path


def in_dirname(path, wanted_parent_dirname):
    """ If the basename of the parent of path is not 'wanted_parent_dirname', 
    create a subfolder 'wanted_parent_dirname' and return pathname in
    this subfolder. """

    current_dir, basename = os.path.split(path)
    if os.path.basename(current_dir) != wanted_parent_dirname:
        new_dir = os.path.join(current_dir, wanted_parent_dirname)
        make_dir(new_dir)
    else:
        new_dir = current_dir

    return os.path.join(new_dir, basename)


def make_dir(new_dir):
    ''' Make a new directory if it doesn't exist already. Create all
    non-existing parents on the way.'''

    sub_dirs = new_dir.split('/')
    current_dir = ''
    if len(sub_dirs[0]) == 0:
        current_dir = '/'
    while len(sub_dirs) > 0:
        current_dir = os.path.join(current_dir, sub_dirs[0])
        if not os.path.exists(current_dir):
            os.mkdir(current_dir)
        sub_dirs.pop(0)


def get_extension(path):
    """Get the extension of a path (including '.').

    Raises an error if there are multiple dots in the
    pathname, and it doesnt end in '.nii', '.mha' or '.gz'"""

    base = os.path.basename(path)
    name, ext = os.path.splitext(base)

    if '.' in name:
        if ext == '.gz':
            _, ext_sub = os.path.splitext(name)
            ext = ext_sub + ext
        elif ext not in ['.nii', '.mha']:
            print
            'Taking %s as extension for %s' % (ext, base)

    return ext


def set_extension(path, extension):
    """ Change the file extension of the path (a dot is automatically
    added if absent in `extension`). """

    if extension[0] != '.':
        extension = '.' + extension

    current_extension = get_extension(path)
    new_path = path.replace(current_extension, extension)

    return new_path


def extend_basename(path, base_extension, binding='_'):
    """ Extend the basename of a path just before the file extension. """

    if not isinstance(base_extension, str):
        err = 'Supplied extension is not a string!'
        raise ValueError(err)

    if len(base_extension) > 0:
        if base_extension[0] != binding:
            base_extension = binding + base_extension

    ext = get_extension(path)
    new_path = path.replace(ext, base_extension + ext)

    return new_path
