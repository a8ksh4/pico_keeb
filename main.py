
import input_encoder
import input_stick
import input_matrix

INPUTS = [input_encoder, input_stick, input_matrix]

def main():
    '''Main program loop...'''
    print("Initializing input moudles...")
    for n, im in enumerate(INPUTS):
        print("Initializing", n, im)
        im.init(n)
    print("Looping on input states")
    for im in INPUTS:
        changes = im.get_changes()
        print(im, changes)
        time.sleep(1000)
    print('foo')


if __name__ == "__main__":
    
    # Your main code logic here
    main()
