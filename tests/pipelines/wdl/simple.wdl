version 1.0

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

# WDL using the Snakemake test file as example.
# Just a simple dummy pipeline that reads some data from /dev/urandom,
# and does some transformations on it.

task read_random {
    input {
        Int lines_to_read
        String outfile_name
    }
    command {
        set -e
        mkdir -p $(dirname ~{outfile_name})
        head -n ~{lines_to_read} /dev/urandom > ~{outfile_name}
    }
    output {
        File out = outfile_name
    }
    runtime {
        docker: "ubuntu:18.04"
    }
}

task base64 {
    input {
        File in_file
        String outfile_name
    }
    command {
        set -e -o pipefail
        mkdir -p $(dirname ~{outfile_name})
        cat ~{in_file} | base64 > ~{outfile_name}
    }
    output {
      File out = outfile_name
    }
    runtime {
       docker: "ubuntu:18.04"
    }
}

task gzip {
    input {
        File in_file
        String outfile_name
    }
    command {
        set -e -o pipefail
        mkdir -p $(dirname ~{outfile_name})
        cat ~{in_file} | gzip -c > ~{outfile_name}
    }
    output {
        File out = outfile_name
    }
    runtime {
        docker: "ubuntu:18.04"
    }

}

task concatenate_files {
    input {
        Array[File]+ files
        String outfile_name
     }
    command {
        set -e
        mkdir -p $(dirname ~{outfile_name})
        cat ~{sep=' ' files} > ~{outfile_name}
    }
    output {
        File out = outfile_name
    }
    runtime {
        docker: "ubuntu:18.04"
    }
}

workflow random_zip {
    input {
        Int lines_to_read
    }

    Array[Int] iterations = range(10)

    scatter (iteration in iterations) {
        call read_random {
            input:
                lines_to_read=lines_to_read,
                outfile_name="rand/" + iteration + ".bin"
        }
        call base64 {
            input:
                in_file = read_random.out,
                outfile_name="b64/" + iteration + ".txt"
        }
        call gzip {
            input:
                in_file = base64.out,
                outfile_name="randgz/" + iteration + ".txt.gz"
        }
    }
    call concatenate_files {
        input:
            files = gzip.out,
            outfile_name="all_data.gz"
    }
    output {
        Array[File] rand_files = read_random.out
        Array[File] base64_files = base64.out
        Array[File] gzip_files = gzip.out
        File zipped_file = concatenate_files.out
    }
}
