version 1.0

task echo {
    input {
        String string
    }
    command {
        echo ~{string}
    }
    output {
        String out = stdout()
    }
}