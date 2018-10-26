import sys
import os
import time

import numpy

from larcv.dataloader2 import larcv_threadio


class larcv_interface(object):
    '''
    This class is just a wrapper around the dataloaders and threadio.  You should not feel
    pressured to use it, the threadio python classes work perfectly well.  However, 
    this class implements the same interface as the distributed_larcv_interface class
    which wraps larcv threadio in mpi4py to allow distributed training. See that class for
    more details.

    The bottom line is, if you want to use distributed_larcv_interface, you can use this class
    for a nearly drop-in replacement in prototyping in environments without  MPI, just on a single
    node.
    '''

    def __init__(self,verbose=False):
        '''init function
        
        Not much to store here, just a dict of dataloaders and the keys to access their data.
        '''
        super().__init__()
        self._dataloaders = {}
        self._data_keys   = {}
        self._dims        = {}
        self._verbose     = verbose



    def prepare_manager(self, mode, io_config, minibatch_size, data_keys):
        '''Prepare a manager for io
        
        Creates an instance of larcv_threadio for a particular file to read.
        
        Arguments:
            mode {str} -- The mode of training to store this threadio under (typically "train" or "TEST" or similar)
            io_config {dict} -- the io config dictionary.  Required keys are: 'filler_name', 'verbosity', and 'filler_cfg'
            data_keys_override {dict} -- If desired, you can override the keys for dataacces,
        
        Raises:
            Exception -- [description]
        '''


        if mode in self._dataloaders:
            raise Exception("Can not prepare manager for mode {}, already exists".format(mode))

        # Check that the required keys are in the io config:
        for req in ['filler_name', 'verbosity', 'filler_cfg']:
            if req not in io_config:
                raise Exception("io_config for mode {} is missing required key {}".format(mode, req))


        start = time.time()

        # Initialize and configure a manager:
        io = larcv_threadio()
        io.configure(io_config)
        io.start_manager(minibatch_size)

        # Save the manager
        self._dataloaders.update({mode : io})
        self._dataloaders[mode].next()

        # Store the keys for accessing this datatype:
        self._data_keys[mode] = data_keys
    
        # Read and save the dimensions of the data:
        self._dims[mode] = {}
        for key in self._data_keys[mode]:
            self._dims[mode][key] = self._dataloaders[mode].fetch_data(self._data_keys[mode][key]).dim()

        self._dataloaders.update({ mode : io})

        end = time.time()

        # Print out how long it took to start IO:
        if self._verbose:
            sys.stdout.write("Time to start {0} IO: {1:.2}s\n".format(mode, end - start))

        return


    def fetch_minibatch_data(self, mode):
        # Return a dictionary object with keys 'image', 'label', and others as needed
        # self._dataloaders['train'].fetch_data(keyword_label).dim() as an example
        this_data = {}
        for key in self._data_keys[mode]:
            this_data[key] = self._dataloaders[mode].fetch_data(self._data_keys[mode][key]).data()
            this_data[key] = numpy.reshape(this_data[key], self._dims[mode][key])

        return this_data

    def fetch_minibatch_dims(self, mode):
        # Return a dictionary object with keys 'image', 'label', and others as needed
        # self._dataloaders['train'].fetch_data(keyword_label).dim() as an example
        return self._dims[mode]

