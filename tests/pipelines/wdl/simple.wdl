version 1.0

task echo {
    input {
        String string
    }
    command {
        echo ~{string}
    }
    output {
        File out = stdout()
    }
}

task zip {
    input {
        File in_file
        String out_path
    }
    command {
        # Do not keep timestamp and original name. So md5sum will evaluate
        # contents only.
        gzip -nc ~{in_file} > ~{out_path}
    }
    output {
      File out_file = out_path
    }
}

workflow string_to_zip {
    input {
        String string
        String out_path
    }
    call echo {
        input:
            string = string
    }
    call zip {
        input:
            in_file=echo.out,
            out_path=out_path
    }

    output {
        File zipped_file = zip.out_file
    }
}