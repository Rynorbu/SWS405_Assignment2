# reverse.py - undo what evilscript.py.py did
# The script did:  output = base64( xor(input, 3) )
# So I do the opposite in reverse order:
#                  input  = xor( base64_decode(output), 3 )
import base64
import sys

KEY = int(sys.argv[2])                                    # XOR key found in the script (^3)

data = open(sys.argv[1], "rb").read()
data = data.replace(b"\x00", b"").strip()                # remove null padding added by dumpfiles
decoded = base64.b64decode(data)                         # step 1: undo base64
original = "".join(chr(b ^ KEY) for b in decoded)        # step 2: undo XOR (XOR is its own inverse)
print(original)
