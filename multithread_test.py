from multiprocessing import Pool

import time

def f(x):
	time.sleep(0.5)
	print x

def main():
	pool = Pool(processes=20)

	start_time = time.time()
	pool.map(f, range(200))
	print "map length: " + str(time.time() - start_time)
	start_time = time.time()
	res = pool.map_async(f, range(200))
	res.get(timeout=100)
	print "map_async length:" + str(time.time() - start_time) 

if __name__ == "__main__":
	main()