#统计系统的 totalram, freeram, shareram
#
#
#



from __future__ import print_function
from time import sleep, strftime
from bcc import BPF


bpf_text = """
    
#include <uapi/linux/ptrace.h>
#include <linux/sched.h>
#include <linux/mm_types.h>
#include <linux/sched/mm.h>

#define PAGE_SHIFT 12
#define K(x) (x) << (PAGE_SHIFT - 10)
BPF_HASH(table_meminfo, unsigned long, unsigned long);

int cul_meminfo(struct pt_regs *ctx, struct sysinfo *val) {
    
    //totalram
    unsigned long temp1 = 1;
    unsigned long totalram_size = val->totalram;
    unsigned long totalram = K(totalram_size);
    table_meminfo.update(&temp1, &totalram);

    //freeram
    unsigned long temp2 = 2;
    unsigned long freeram_size = val->freeram;
    unsigned long freeram = K(freeram_size);
    table_meminfo.update(&temp2, &freeram);

    
    //sharedram
    unsigned long temp3 = 3;
    unsigned long shared_size = val->sharedram;
    unsigned long sharedram = K(shared_size);
    table_meminfo.update(&temp3, &sharedram);


    //buffer
    //unsigned long temp4 = 4;
    //unsigned long buffer_size = val->bufferram;
    //unsigned long bufferram = K(buffer_size);
    //table_meminfo.update(&temp4, &bufferram);




    return 0;
}


"""

b = BPF(text = bpf_text)
table_meminfo = b.get_table("table_meminfo")

b.attach_kprobe(event="si_swapinfo", fn_name="cul_meminfo")

while(1):
    sleep(1)
    for k, v in table_meminfo.items():
        if(k.value == 1):
            print("totalram :%lu"%(v.value))
        if(k.value == 2):
            print("freeram: %lu"%(v.value))
        if(k.value == 3):
            print("sharedram: %lu"%(v.value))
