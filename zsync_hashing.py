import hashlib
import zlib

stronghash = hashlib.md5
_PRIME_MOD = 65521

"""
Receives the unsigned integers "checksum", "removed" and "added", as well as a blocksize
Generates the Adler-32 checksum for the new value using the old checksum, the removed value and the added value
"""
def adler32_roll(checksum, removed, added, blocksize):
	a = checksum & 0xffff
	b = (checksum >> 16) & 0xffff
	a += added - removed % _PRIME_MOD
	b += a - 1 - (removed * blocksize) % _PRIME_MOD
	return (b << 16) | a #, a, b

"""
Receives a bytearray "data"
Returns the Adler-32 checksum of that bytearray
https://en.wikipedia.org/wiki/Adler-32
"""
def adler32(data):
	return zlib.adler32(data)
	checksum = zlib.adler32(data)
	a = checksum & 0xffff
	b = (checksum >> 16) & 0xffff
	return (b << 16) | a, a, b

"""
A small test using a paragraph of Lorem Ipsum
"""
if __name__ == "__main__":
	text = """Vivamus accumsan mi at velit porta mollis. Pellentesque a sem non justo rutrum iaculis. Phasellus facilisis vestibulum ipsum eu efficitur. Mauris ac rhoncus enim, sollicitudin ullamcorper magna. Nullam sed augue fringilla, consequat eros sit amet, auctor justo. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Morbi non lectus a arcu consequat vestibulum. Praesent malesuada varius nisl tincidunt ullamcorper. Aenean laoreet, turpis vel venenatis tincidunt, magna risus pulvinar ante, ut ultrices nisi eros ut dui. Sed nec lacinia ligula. Pellentesque lobortis porttitor elementum. Vivamus et pellentesque urna, vitae iaculis tortor. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed sed lacus vel elit suscipit placerat. Fusce consequat dui id rhoncus fermentum."""
	# in decimal it should be 1763320641
	data = bytearray(text, "UTF-8")	
	expected = adler32(data[1:])
	first = adler32(data[:-1])
	obtained = adler32_roll(first, data[0], data[-1], len(data)-1)
	print("Expected: "+str(expected))
	print("Obtained: "+str(obtained))
