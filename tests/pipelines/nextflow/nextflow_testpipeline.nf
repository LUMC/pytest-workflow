#!/usr/bin/env nextflow

# Copyright (C) 2018 Leiden University Medical Center
# This file is part of pytest-workflow
#
# pytest-workflow is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# pytest-workflow is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with pytest-workflow.  If not, see <https://www.gnu.org/licenses/

# Nextflow using the Snakemake test file as example.
# Just a simple dummy pipeline that reads some data from /dev/urandom,
# and does some transformations on it.

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
