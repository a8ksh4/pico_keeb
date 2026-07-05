
import input_encoder_pio
import input_stick_pio
import input_matrix
import input_adxl
from time import sleep

INPUTS = [input_encoder_pio, input_stick_pio, input_matrix, input_adxl]
# If pio machines are too many instructions, different
# clocks, ..., they need to be on separate pio blocks.
PIO_MAP = [0, 4, None, None]


def main():
    '''Main program loop...'''
    print("Initializing input moudles...")
    for im, n in zip(INPUTS, PIO_MAP):
        print("Initializing", im, n)
        im.init(n)
        print(dir(im))

    print("Looping on input states")
    while True:
        state = {'keys': [], 'mouse': (0, 0), 'wheel': []}
        for im in INPUTS:
            changes = im.get_state()
            print(im.__name__, changes)
            if 'keys' in changes:
                state['keys'].extend(changes['keys'])
            if 'mouse' in changes:
                state['mouse'] = (state['mouse'][0] + changes['mouse'][0],
                                  state['mouse'][1] + changes['mouse'][1])
            if 'wheel' in changes:
                state['wheel'].extend(changes['wheel'])
        print()
        print(state)
        print()
        sleep(1)
    print('foo')



if __name__ == "__main__":
    
    # Your main code logic here
    main()
