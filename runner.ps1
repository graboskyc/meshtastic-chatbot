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

#python3 test.py

docker stop meshtasticbot
docker rm meshtasticbot
docker run -t -i -d --name meshtasticbot -e "MDBURI=$env:MDBURI" -e "EMAIL=$env:EMAIL" -e "LOCLAT=$env:LOCLAT" -e "LOCLONG=$env:LOCLONG" -e "CHANIND=$env:CHANIND" -e "INTERFACE=$env:INTERFACE" -e "SUMBOTURI=$env:SUMBOTURI" --restart unless-stopped graboskyc/meshtasticbot:latest
