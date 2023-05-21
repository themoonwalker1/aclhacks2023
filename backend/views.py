# Import necessary libraries and modules
from django.http import JsonResponse
from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister, execute, BasicAer
from qiskit.tools.visualization import plot_histogram
import numpy as np
from .models import QuantumModel

alice = None  # Reference to the quantum computing model
bob = None
alice_key = None
alice_table = None

n = 16

# Quantum circuit for Alice state

def SendState(qc1, qc2, qr, cr):
    ''' This function takes the output of a circuit qc1 (made up only of x and
        h gates and initializes another circuit qc2 with the same state
    '''

    qs = qc1.qasm().split(sep=';')[4:-1]

    for index, instruction in enumerate(qs):
        qs[index] = instruction.lstrip()

    for instruction in qs:
        if instruction[0] == 'x':
            old_qr = int(instruction[5:-1])
            qc2.x(qr[old_qr])
        elif instruction[0] == 'h':
            old_qr = int(instruction[5:-1])
            qc2.h(qr[old_qr])
        elif instruction[0] == 'm':
            pass
        else:
            raise Exception('Unable to parse instruction')


def encrypt(request):
    global alice, alice_key, alice_table, bob

    try:
        message = request.GET['message']
    except Exception:
        return JsonResponse({'success': False, 'error': 'No message'})

    qr = QuantumRegister(n, name='qr')
    cr = ClassicalRegister(n, name='cr')

    # Quantum circuit for alice state
    alice = QuantumCircuit(qr, cr, name='Alice')

    # Generate a random number in the range of available qubits [0,65536))
    alice_key = np.random.randint(0, high=2 ** n)

    # Cast key to binary for encoding
    # range: key[0]-key[15] with key[15] least significant figure
    alice_key = np.binary_repr(alice_key, n)  # n is the width

    # Encode key as alice qubits
    # IBM's qubits are all set to |0> initially
    for index, digit in enumerate(alice_key):
        if digit == '1':
            alice.x(qr[index])  # if key has a '1', change state to |1>

    # Switch randomly about half qubits to diagonal basis
    alice_table = []  # Create empty basis table
    for index in range(len(qr)):  # BUG: enumerate(q) raises an out of range error
        if 0.5 < np.random.random():  # With 50% chance...
            alice.h(qr[index])  # ...change to diagonal basis
            alice_table.append('X')  # character for diagonal basis
        else:
            alice_table.append('Z')  # character for computational basis

    # get_qasm method needs the str label
    # alternatively we can use circuits[0] but since dicts are not ordered
    # it is not a good idea to put them in a func
    # circuits = list(qp.get_circuit_names())

    # print(type(alice))
    # print(type(alice_key))
    # print(type(alice_table))
    # print(type(bob))

    bob = QuantumCircuit(qr, cr, name='Bob')

    SendState(alice, bob, qr, cr)

    qm = QuantumModel()
    qm.set_alice_circuit(alice)
    qm.set_bob_circuit(bob)
    qm.set_alice_key(alice_key)
    qm.alice_table = alice_table
    qm.message = message
    qm.save()

    return JsonResponse({'key': str(qm.key)})
def decrypt(request, hex_code):
    qr = QuantumRegister(n, name='qr')
    cr = ClassicalRegister(n, name='cr')
    try:
        # Retrieve the QuantumModel object based on the hex_code
        qm = QuantumModel.objects.get(key=hex_code)
        # print(qm.bob)
        # print(QuantumCircuit.from_qasm_str(qm.bob))
    except QuantumModel.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Invalid hex code'})

    # alice = qm.get_alice_circuit()
    bob = qm.get_bob_circuit()
    alice_key = qm.get_alice_key()
    alice_table = qm.alice_table

    # print(bob)
    print(alice_key)
    print(alice_table)

    # Bob doesn't know which basis to use
    bob_table = []
    for index in range(len(qr)):
        if 0.5 < np.random.random():  # With 50% chance...
            bob.h(qr[index])  # ...change to diagonal basis
            bob_table.append('X')
        else:
            bob_table.append('Z')

    # Measure all qubits
    for index in range(len(qr)):
        bob.measure(qr[index], cr[index])

    # Execute the quantum circuit
    backend = BasicAer.get_backend('qasm_simulator')
    result = execute(bob, backend=backend, shots=1).result()
    plot_histogram(result.get_counts(bob))

    # Result of the measure is Bob's key candidate
    bob_key = list(result.get_counts(bob))[0]
    bob_key = bob_key[::-1]  # key is reversed so that first qubit is the first element of the list

    print(alice_key)
    print(bob_key)

    keep = []
    discard = []
    for qubit, basis in enumerate(zip(alice_table, bob_table)):
        if basis[0] == basis[1]:
            print("Same choice for qubit: {}, basis: {}".format(qubit, basis[0]))
            keep.append(qubit)
        else:
            print("Different choice for qubit: {}, Alice has {}, Bob has {}".format(qubit, basis[0], basis[1]))
            discard.append(qubit)

    print(type(alice_key))
    print(type(bob_key))

    new_alice_key = [alice_key[qubit] for qubit in keep]
    new_bob_key = [bob_key[qubit] for qubit in keep]

    acc = 0
    for bit in zip(new_alice_key, new_bob_key):
        if bit[0] == bit[1]:
            acc += 1

    print('Percentage of qubits to be discarded according to table comparison: ', len(keep) / n)
    print('Measurement convergence by additional chance: ', acc / n)

    new_alice_key = [alice_key[qubit] for qubit in keep]
    new_bob_key = [bob_key[qubit] for qubit in keep]

    acc = 0
    for bit in zip(new_alice_key, new_bob_key):
        if bit[0] == bit[1]:
            acc += 1

    print('Percentage of similarity between the keys: ', acc / len(new_alice_key))

    ak = "".join(new_alice_key)
    rem = 8 - (len(ak) % 8)
    ak = "".join(["1" for _ in range(rem)] + [ak])

    bk = "".join(new_alice_key)
    rem = 8 - (len(bk) % 8)
    bk = "".join(["1" for _ in range(rem)] + [bk])

    print(ak)
    print(bk)
    return JsonResponse({'alice_message_encrypted': encrypt_string(qm.message, ak), 'new_bob_key': new_bob_key, 'success': acc / len(new_alice_key) > 0.9 , "test": decrypt_string(encrypt_string(qm.message, bk), bk), "similarity" : acc / len(new_alice_key), "discarded" : len(keep) / n })

def encrypt_string(string, key):
    # Convert the string to binary format
    string_bin = ''.join(format(ord(c), '08b') for c in string)

    # Repeat or pad the key to match the length of the string binary
    key_bin = (key * (len(string_bin) // len(key))) + key[:len(string_bin) % len(key)]

    # Perform bitwise XOR between the string binary and key
    encrypted_bin = ''.join(str(int(a) ^ int(b)) for a, b in zip(string_bin, key_bin))

    # Convert the encrypted binary back to string format
    encrypted_string = ''.join(chr(int(encrypted_bin[i:i+8], 2)) for i in range(0, len(encrypted_bin), 8))

    return encrypted_string


def decrypt_string(encrypted_string, key):
    # Convert the encrypted string to binary format
    encrypted_bin = ''.join(format(ord(c), '08b') for c in encrypted_string)

    # Repeat or pad the key to match the length of the encrypted binary
    key_bin = (key * (len(encrypted_bin) // len(key))) + key[:len(encrypted_bin) % len(key)]

    # Perform bitwise XOR between the encrypted string and key
    decrypted_bin = ''.join(str(int(a) ^ int(b)) for a, b in zip(encrypted_bin, key_bin))

    # Convert the decrypted binary back to string format
    decrypted_string = ''.join(chr(int(decrypted_bin[i:i+8], 2)) for i in range(0, len(decrypted_bin), 8))

    return decrypted_string
