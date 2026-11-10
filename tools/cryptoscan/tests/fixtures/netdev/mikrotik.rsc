# nov/10/2026 10:00:00 by RouterOS 6.49.10
# software id = ABCD-EFGH
#
# model = RB4011iGS+
/system identity
set name=mt-branch-03
/ip service
set telnet disabled=no
set ftp disabled=yes
set www disabled=no
set ssh disabled=no
set api disabled=yes
/ip ssh
set strong-crypto=no
/snmp
set enabled=yes
/snmp community
set [ find default=yes ] name=PLACEHOLDER-COMM
add authentication-protocol=MD5 encryption-protocol=DES name=monitor security=private
/ip ipsec profile
set [ find default=yes ] dh-group=modp1024 enc-algorithm=3des hash-algorithm=md5
/ip ipsec peer
add address=192.0.2.1/32 exchange-mode=aggressive name=hq
/ip ipsec proposal
set [ find default=yes ] auth-algorithms=md5 enc-algorithms=des pfs-group=modp768
/user
add name=ops group=full password=PLACEHOLDER
