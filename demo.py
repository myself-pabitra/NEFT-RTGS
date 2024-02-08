import dns.resolver

resolver1_opendns_ip = False
resolver = dns.resolver.Resolver()
opendns_result = resolver.resolve("resolver1.opendns.com", "A")
for record in opendns_result:
    resolver1_opendns_ip = record.to_text()

if resolver1_opendns_ip:
    resolver.nameservers = [resolver1_opendns_ip]
    myip_result = resolver.resolve("myip.opendns.com", "A")
    for record in myip_result:
        print(f"Your external ip is {record.to_text()}")
