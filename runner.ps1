get-content .env | foreach {
    $index = $_.IndexOf('=');
        $key = ''
        $value =''
        if ($index -ge 0) {
            $key = $_.Substring(0, $index)
            $value = $_.Substring($index + 1)
    }
    set-content env:\$key $value.replace('"','')
    Write-Output "Setting Env Flag for $key"
}

python3 test.py