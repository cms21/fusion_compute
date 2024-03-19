from performance_test import make_sequential_test,make_delay_test
from performance_test import assemble_ionorb_input_kwargs

if __name__ == '__main__':
    inputs = assemble_ionorb_input_kwargs(testfile="collection_of_multi-slice_shots.txt",
                                          nparts=[50000])
    #inputs = assemble_ionorb_input_kwargs(nparts=[1000,10000])

    #make_sequential_test(inputs, machines=["polaris"],niter=1)
    make_delay_test(inputs, machines=["perlmutter"],niter=1)
