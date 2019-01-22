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
        gzip -c ~{in_file} > out_file
    }
    File out_file = out_path
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