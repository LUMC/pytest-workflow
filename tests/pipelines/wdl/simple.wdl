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
    }
    command {
        head -n ~{lines_to_read} /dev/urandom > output
    }
    output {
        File out = "output"
    }
    runtime {
        docker: "ubuntu:18.04"
    }
}

task base64 {
    input {
        File in_file
    }
    command {
        cat ~{in_file} | base64 > output.txt
    }
    output {
      File out = "output.txt"
    }
    runtime {
       docker: "ubuntu:18.04"
    }
}

task gzip {
    input {
        File in_file
    }
    command {
        cat in_file | gzip -c > output.gz
    }
    output {
        File out = "output.gz"
    }
    runtime {
        docker: "ubuntu:18.04"
    }

}

task concatenate_gzip_files {
    input {
        Array[File]+ files

    }
    command {
        cat ~{sep=' ' files} > output.gz
    }
    output {
        File out = "output.gz"
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
                lines_to_read=lines_to_read
        }
        call base64 {
            input:
                in_file = read_random.out
        }
        call gzip {
            input:
                in_file = base64.out
        }
    }
    call concatenate_gzip_files {
        input:
            files = gzip.out
    }
    output {
        File zipped_file = concatenate_gzip_files.out
    }
}
