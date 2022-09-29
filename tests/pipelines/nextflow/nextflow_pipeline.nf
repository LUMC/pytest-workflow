#!/usr/bin/env nextflow

params.N_LINES_TO_READ = 5

process read_random {
	publishDir 'results/rand'

	input:
	val iter
	output: 
	val iter
	path "rand_${iter}.txt"
	script:
	"""
	head -n ${params.N_LINES_TO_READ} /dev/urandom > rand_${iter}.txt
	"""
}

process base64_random {
	publishDir 'results/b64'

	input:
	val iter
	path "rand_${iter}.txt"
	output:
	val iter
	path "b64_${iter}.txt"
	script:
	"""
	cat rand_${iter}.txt | base64 > b64_${iter}.txt
	"""
}

process gzip_b64 {
	publishDir 'results/randgz'

	input:
	val iter
	path "b64_${iter}.txt"
	output:
	path "randgz_${iter}.txt.gz"
	script:
	"""
	cat b64_${iter}.txt | gzip -c > randgz_${iter}.txt.gz
	"""
}

process concat_gzip {
	publishDir 'results'

	input:
	path 'x'
	output:
	path "all_data.gz"
	script:
	"""
	cat ${x} > all_data.gz
	"""
}

workflow {
	iterations = channel.from(0..9) | read_random | base64_random | gzip_b64
	gzip_b64.out.collect() | concat_gzip
}
