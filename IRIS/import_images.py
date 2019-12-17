#!/usr/bin/env python3
"""
This model is used to import the images and store them into a 3D matrix.

We prepare two strategies to parse the different techniques of in situ sequencing, which published by R Ke (R Ke,
Nat. Methods, 2013) and KH Chen (Chen et al, Science, 2015).

Here, Ke's data is employed as the major data structure in our software. In this data
structure, barcodes are composed of 4 types of pseudo-color, representing the A, T, C, G bases. In addition there's a
DAPI background.

Our software generate a 3D matrix to store all the images. Each channel is made of a image matrix, and insert into this
tensor in the order of cycle
"""


from sys import stderr
from cv2 import (imread, imwrite,
                 add, addWeighted, warpAffine,
                 IMREAD_GRAYSCALE)
from numpy import (array, uint8)

from .register_images import register_cycles


def decode_data_Ke(f_cycles):
    """
    For parsing data generated by the technique described in Ke et al, Nature Methods (2013).

    Input the directories of cycle.
    Returning a pixel matrix which contains all the gray scales of image pixel as well as their coordinates.

    :param f_cycles: The image directories in sequence of cycles, of which the different channels are stored.
    :return: A tuple including a 3D matrix and a background image matrix.
    """
    if len(f_cycles) < 1:
        print('ERROR CYCLES', file=stderr)

        exit(1)

    f_cycle_stack = []

    f_std_img = array([], dtype=uint8)
    reg_ref = array([], dtype=uint8)

    for cycle_id in range(0, len(f_cycles)):
        adj_img_mats = []

        ####################################
        # Read five channels into a matrix #
        ####################################
        channel_A = imread('/'.join((f_cycles[cycle_id], 'Y5.tif')),   IMREAD_GRAYSCALE)
        channel_T = imread('/'.join((f_cycles[cycle_id], 'FAM.tif')),  IMREAD_GRAYSCALE)
        channel_C = imread('/'.join((f_cycles[cycle_id], 'TXR.tif')),  IMREAD_GRAYSCALE)
        channel_G = imread('/'.join((f_cycles[cycle_id], 'Y3.tif')),   IMREAD_GRAYSCALE)
        channel_0 = imread('/'.join((f_cycles[cycle_id], 'DAPI.tif')), IMREAD_GRAYSCALE)
        ####################################

        #########################################################################################
        # Merge different channels from a same cycle into one matrix for following registration #
        #                                                                                       #
        # BE CARE: The parameters 'alpha' and 'beta' maybe will affect whether the registering  #
        # success. Sometimes, a registration would succeed with only using DAPI from different  #
        # cycle instead of merged images                                                        #
        #########################################################################################
        merged_img = channel_0
        ########

        ###############################
        # Block of alternative option #
        ###############################
        # alpha = 0.5
        # beta = 0.6
        # merged_img = addWeighted(add(add(add(channel_A, channel_T), channel_C), channel_G), alpha, channel_0, beta, 0)
        ###############################

        if cycle_id == 0:
            reg_ref = merged_img

            ###################################
            # Output background independently #
            ###################################
            foreground = add(add(add(channel_A, channel_T), channel_C), channel_G)
            background = channel_0

            f_std_img = addWeighted(foreground, 0.4, background, 0.6, 0)
            ########
            # f_std_img = foreground
            # f_std_img = addWeighted(foreground, 0.5, background, 0.5, 0)  # Alternative option
            # f_std_img = addWeighted(foreground, 0.4, background, 0.8, 0)  # Alternative option
            ###################################

        trans_mat = register_cycles(reg_ref, merged_img, 'ORB')

        #############################
        # For registration checking #
        #############################
        debug_img = warpAffine(merged_img, trans_mat, (reg_ref.shape[1], reg_ref.shape[0]))

        debug_img = uint8(debug_img)
        # imwrite('debug.cycle_' + str(int(cycle_id + 1)) + '.tif', merged_img)
        imwrite('debug.cycle_' + str(int(cycle_id + 1)) + '.reg.tif', debug_img)
        #############################

        channel_A = warpAffine(channel_A, trans_mat, (reg_ref.shape[1], reg_ref.shape[0]))
        channel_T = warpAffine(channel_T, trans_mat, (reg_ref.shape[1], reg_ref.shape[0]))
        channel_C = warpAffine(channel_C, trans_mat, (reg_ref.shape[1], reg_ref.shape[0]))
        channel_G = warpAffine(channel_G, trans_mat, (reg_ref.shape[1], reg_ref.shape[0]))

        adj_img_mats.append(channel_A)
        adj_img_mats.append(channel_T)
        adj_img_mats.append(channel_C)
        adj_img_mats.append(channel_G)
        #########################################################################################

        ###################################################################################################
        # This stacked 3D-tensor is a common data structure for following analysis and data compatibility #
        ###################################################################################################
        f_cycle_stack.append(adj_img_mats)
        ###################################################################################################

    return f_cycle_stack, f_std_img


def decode_data_Chen(f_cycles):
    """
    For parsing data generated by the technique described in Chen et al, Science (2015).

    Input the directories of cycle.
    Returning a pixel matrix which contains all the gray scales of image pixel as well as their coordinates.

    :param f_cycles: The image directories in sequence of cycles, of which the different channels are stored.
    :return: A tuple including a 3D matrix and a background image matrix.
    """
    if len(f_cycles) < 1:
        print('ERROR CYCLES', file=stderr)

        exit(1)

    f_cycle_stack = []

    f_std_img = array([], dtype=uint8)

    for cycle_id in range(0, len(f_cycles)):
        adj_img_mats = []

        ####################################
        # Read five channels into a matrix #
        ####################################
        channel_0 = imread('/'.join((f_cycles[cycle_id], 'STORM.tif')), IMREAD_GRAYSCALE)
        ####################################

        #########################################################################################
        # Merge different channels from a same cycle into one matrix for following registration #
        #                                                                                       #
        # A registration would succeed with only using DAPI from different cycle instead of     #
        # merged images                                                                         #
        #########################################################################################
        merged_img = channel_0

        if cycle_id == 0:
            ###################################
            # Output background independently #
            ###################################
            f_std_img = channel_0
            ###################################

        # trans_mat = register_cycles(reg_ref, merged_img, 'ORB')  # Don't need registration

        ########################
        # For merging checking #
        ########################
        imwrite('debug.cycle_' + str(int(cycle_id + 1)) + '.tif', merged_img)
        ########################

        adj_img_mats.append(channel_0)
        #########################################################################################

        ###################################################################################################
        # This stacked 3D-tensor is a common data structure for following analysis and data compatibility #
        ###################################################################################################
        f_cycle_stack.append(adj_img_mats)
        ###################################################################################################

    return f_cycle_stack, f_std_img


if __name__ == '__main__':
    pass
