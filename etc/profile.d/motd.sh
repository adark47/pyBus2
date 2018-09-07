#!/bin/bash
# Based on https://github.com/gagle/raspberrypi-motd/blob/master/motd.sh

function color (){
  echo "\e[$1m$2\e[0m"
}

function extend (){
  local str="$1"
  let spaces=74-${#1}
  while [ $spaces -gt 0 ]; do
    str="$str "
    let spaces=spaces-1
  done
  echo "$str"
}

function center (){
  local str="$1"
  let spacesLeft=(85-${#1})/2
  let spacesRight=78-spacesLeft-${#1}
  while [ $spacesLeft -gt 0 ]; do
    str=" $str"
    let spacesLeft=spacesLeft-1
  done

  while [ $spacesRight -gt 0 ]; do
    str="$str "
    let spacesRight=spacesRight-1
  done

  echo "$str"
}

function sec2time (){
  local input=$1

  if [ $input -lt 60 ]; then
    echo "$input seconds"
  else
    ((days=input/86400))
    ((input=input%86400))
    ((hours=input/3600))
    ((input=input%3600))
    ((mins=input/60))

    local daysPlural="s"
    local hoursPlural="s"
    local minsPlural="s"

    if [ $days -eq 1 ]; then
      daysPlural=""
    fi

    if [ $hours -eq 1 ]; then
      hoursPlural=""
    fi

    if [ $mins -eq 1 ]; then
      minsPlural=""
    fi

    echo "$days day$daysPlural, $hours hour$hoursPlural, $mins minute$minsPlural"
  fi
}

borderColor=34
headerLeafColor=32
headerRaspberryColor=34
greetingsColor=36
statsLabelColor=31
whiteColor=97

borderLine="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
borderTopLine=$(color $borderColor "┏$borderLine┓")
borderBottomLine=$(color $borderColor "┗$borderLine┛")
borderBar=$(color $borderColor "┃")
borderEmptyLine="$borderBar                                                                                              $borderBar"

# Header
header="$borderTopLine\n$borderEmptyLine\n"
header="$header$borderBar$(color $headerRaspberryColor "    ___ __  ____      __  __  __ _   _ _  _____ ___ __  __ ___ ___ ___   _         _   ___    ")$borderBar\n"
header="$header$borderBar$(color $headerRaspberryColor "   | _ )  \/  \ \    / / |  \/  | | | | ||_   _|_ _|  \/  | __|   \_ _| /_\   __ _/ | |_  )   ")$borderBar\n"
header="$header$borderBar$(color $headerRaspberryColor "   | _ \ |\/| |\ \/\/ /  | |\/| | |_| | |__| |  | || |\/| | _|| |) | | / _ \  \ V / |_ / /    ")$borderBar\n"
header="$header$borderBar$(color $headerRaspberryColor "   |___/_|  |_| \_/\_/   |_|  |_|\___/|____|_| |___|_|  |_|___|___/___/_/ \_\  \_/|_(_)___|   ")$borderBar\n"
header="$header$borderBar$(color $headerRaspberryColor "                                                                                              ")$borderBar"

me=$(whoami)

hostnaam=$(hostname)
kernel=$(uname -ro)
ip="$(ifconfig | grep -A 1 'eth0' | tail -1 | cut -d ':' -f 2 | cut -d ' ' -f 1)"
system="$hostnaam, ($ip), $kernel"

stdinsessions=$(who -m | wc -l)
totalsessions=$(who -l | wc -l)
loggedinsessions=$(who -u | wc -l)
deadsessions=$(who -d | wc -l)
sessions="$totalsessions(total), $loggedinsessions(logins), $stdinsessions(interactive), $deadsessions (dead)"
pybus=$(systemctl is-active pyBus)
bluetoothd=$(systemctl is-active bluetooth)
bluetoothAgent=$(systemctl is-active bluetooth-agent)
shairportSync=$(systemctl is-active shairport-sync)
dacpClient=$(systemctl is-active dacp_client)

totalnumberofprocesses=$(ps -Afl | wc -l)
numberofprocessesroot=$(ps -Afl | grep root | wc -l)
numberofprocesses=$(ps -Afl | grep $me | wc -l)
process="$totalnumberofprocesses(total), $numberofprocessesroot(root), $numberofprocesses(yours)"

# Greetings
greetings="$borderBar$(color $greetingsColor "$(center "Welcome back, $me!")                ")$borderBar\n"
greetings="$greetings$borderBar$(color $greetingsColor "$(center "$(date +"%A, %d %B %Y, %T")")                ")$borderBar"

# System information
read loginFrom loginIP loginDate <<< $(last -F $me | awk 'NR==1 { print $2," (" $3 ") ",$4 " " $5 " " $6 " " $8 " / " $7 }')

if [[ $loginFrom == tty ]]; then
  read loginFrom loginIP loginDate <<< $(last -F $me | awk 'NR==1 { print $2,"local",$3 " " $4 " " $5 " " $7 " / " $6 }')
fi

logins="$loginFrom $loginIP $loginDate"

label1="$(extend "$logins")"
label1="$borderBar  $(color $statsLabelColor "Last Login......:") $label1$borderBar"

uptime="$(sec2time $(cut -d "." -f 1 /proc/uptime))"
uptime="$uptime ($(date -d "@"$(grep btime /proc/stat | cut -d " " -f 2) +"%d-%m-%Y %H:%M:%S"))"

label2="$(extend "$uptime")"
label2="$borderBar  $(color $statsLabelColor "Uptime..........:") $label2$borderBar"

label3="$(extend "$(free -m | awk 'NR==2 { printf "Total: %sMB, Used: %sMB, Free: %sMB",$2,$3,$4; }')")"
label3="$borderBar  $(color $statsLabelColor "Memory..........:") $label3$borderBar"

label4="$(extend "$(df -h ~ | awk 'NR==2 { printf "Total: %sB, Used: %sB, Free: %sB",$2,$3,$4; }')")"
label4="$borderBar  $(color $statsLabelColor "Home space......:") $label4$borderBar"

label5="$(extend "$(/opt/vc/bin/vcgencmd measure_temp | cut -c "6-9")ºC")"
label5="$borderBar  $(color $statsLabelColor "Temperature.....:") $label5$borderBar"

label6="$(extend "$process")"
label6="$borderBar  $(color $statsLabelColor "Processes.......:") $label6$borderBar"

label7="$(extend "$sessions")"
label7="$borderBar  $(color $statsLabelColor "Sessions........:") $label7$borderBar"

label8="$(extend "$system")"
label8="$borderBar  $(color $statsLabelColor "System..........:") $label8$borderBar"

label9="$borderBar  $(color $whiteColor "Services running:                                                                          ") $label9$borderBar"

label10="$(extend "$pybus")"
label10="$borderBar  $(color $statsLabelColor "PyBus...........:") $label10$borderBar"

label11="$(extend "$bluetoothd")"
label11="$borderBar  $(color $statsLabelColor "Bluetooth.......:") $label11$borderBar"

label12="$(extend "$bluetoothAgent")"
label12="$borderBar  $(color $statsLabelColor "Bluetooth-agent.:") $label12$borderBar"

label13="$(extend "$shairportSync")"
label13="$borderBar  $(color $statsLabelColor "Shairport-sync..:") $label13$borderBar"

label14="$(extend "$dacpClient")"
label14="$borderBar  $(color $statsLabelColor "DACP Client.....:") $label14$borderBar"

stats="$label8\n$label1\n$label7\n$label2\n$label6\n$label3\n$label4\n$label5\n$label9\n$label10\n$label11\n$label12\n$label13\n$label14"

# Print motd
echo -e "$header\n$borderEmptyLine\n$greetings\n$borderEmptyLine\n$stats\n$borderEmptyLine\n$borderBottomLine"
