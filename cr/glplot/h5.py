import numpy as np
import h5py
import os.path

def load_hdf5(file):
    f = h5py.File(file, "r")
    data = f["RawData"]
    return data
    
def read_hdf5(data, fromtime, duration):
    channels = data.attrs["channels"]
    freq = data.attrs["freq"]
    fromrow = int(round(fromtime * freq))
    torow = int(round((fromtime + duration) * freq))
    return data[fromrow:torow + 1]

def close_hdf5(data):
    data.file.close()

    
    

def convert_to_hdf5(fromfile, tofile, channels, freq, dtype=None):
    """
    Convert a binary array file, in the format of neuroscope, to a HDF5 file,
    useful for reading the array efficiently from the disk without loading the
    full array in memory.
    Conversion takes roughly ~20s/GB.
    
    Parameters:
    
    ``fromfile``
        
        Path of the initial DAT file containing the binary array.
    
    ``tofile``
        
        Path of the HDF5 file.
    
    ``channels``
        
        Number of channels.
    
    ``freq``
        
        Sampling frequency.
    
    ``dtype``
        
        Numpy dtype of the DAT file, also used for the HDF5 file.
        By default: int16 (2 bytes/sample).
    """
    if dtype is None:
        dtype = np.dtype(np.int16)
    itemsize = dtype.itemsize  # number of bytes per item
    chunkdur = 60  # duration in seconds of each chunk to load
    chunksize = chunkdur * freq * itemsize * channels
    totalsize = os.path.getsize(fromfile)  # size in bytes of fromfile
    totalrows = totalsize / (itemsize * channels)  # total number of rows
    f = open(fromfile, "rb")  # open from file
    f5 = h5py.File(tofile)  # open to file
    # create a HDF5 dataset with extendable size
    d = f5.create_dataset("RawData", (0, channels), \
                          dtype=dtype, maxshape=(None, channels))
    # attributes
    d.attrs["channels"] = channels  # number of channels
    d.attrs["freq"] = freq  # sampling frequency
    d.attrs["duration"] = float(totalrows - 1)/freq
    currow = 0
    print "Convert binary file <%s> to HDF5 file <%s>" % (fromfile, tofile)
    report = ProgressReporter("text")
    report.start()
    while True:
        s = f.read(chunksize)  # read chunksize bytes from the to file
        if not s:
            break
        x = np.fromstring(s, dtype=dtype)  # convert to a Numpy array
        x = x.reshape((-1, channels))  # and resize it
        h = x.shape[0]
        d.resize(currow + h, axis=0)  # extend the HDF5 file
        d[currow:currow + h,:] = x  # put the temp array in the HDF5 file
        report.update(float(currow)/totalrows)
        currow += h
    f.close()
    f5.close()
    report.finish()


