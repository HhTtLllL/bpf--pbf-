from __future__ import print_function
from time import sleep, strftime
from bcc import BPF

#查看多种虚拟内存的统计信息
bpf_text = """

#include <uapi/linux/ptrace.h>
#include <uapi/linux/bpf.h>
#include <linux/mm.h>
#include <linux/seq_file.h>
#include <linux/page_ext.h>
#include <linux/page_owner.h>

BPF_HASH(vmstat, unsigned long, unsigned long);

int allpage(struct pt_regs *ctx, struct seq_file *m, void *arg) {
    
    unsigned long *l = arg;
    unsigned long tmp = *l;
    unsigned long off = l - (unsigned long *)m->private;

    if (off >= 0 && off <= 16) {
        
        vmstat.update(&off, &tmp);
    }

    if ( (off >= 58 && off <= 61) || 
         (off >= 74 && off <= 80) || 
         (off >= 122 && off <= 123) )     

        vmstat.update(&off, &tmp);

    //bpf_trace_printk("name = %d", off);
    //bpf_trace_printk("l = %lu", off);
    
    return 0;
}

"""

name = [
	# enum zone_stat_item counters 
	"nr_free_pages",                #空闲内存页数   0
	"nr_zone_inactive_anon",        #非活跃的页数
	"nr_zone_active_anon",          #活跃的页数
	"nr_zone_inactive_file",        #非活跃的文件页数
	"nr_zone_active_file",          #活跃的文件页数
	"nr_zone_unevictable",
	"nr_zone_write_pending",
	"nr_mlock",
	"nr_bounce",
	"nr_zspages",
	"nr_free_cma",

	# enum numa_stat_item counters 
	"numa_hit",                     #分配page的node与期望的node一致的次数
	"numa_miss",                    #不一致的次数
	"numa_foreign",
	"numa_interleave",
	"numa_local",                   #分配的page的node与当前执行缺页的node一致的次数
	"numa_other",                   #不一致的次数

	# enum node_stat_item counters 
	"nr_inactive_anon",
	"nr_active_anon",
	"nr_inactive_file",
	"nr_active_file",
	"nr_unevictable",
	"nr_slab_reclaimable",
	"nr_slab_unreclaimable",
	"nr_isolated_anon",
	"nr_isolated_file",
	"workingset_nodes",
	"workingset_refault_anon",
	"workingset_refault_file",
	"workingset_activate_anon",
	"workingset_activate_file",
	"workingset_restore_anon",
	"workingset_restore_file",
	"workingset_nodereclaim",

	"nr_anon_pages",
	"nr_mapped",
	"nr_file_pages",
	"nr_dirty",
	"nr_writeback",
	"nr_writeback_temp",
	"nr_shmem",
	"nr_shmem_hugepages",
	"nr_shmem_pmdmapped",
	"nr_file_hugepages",
	"nr_file_pmdmapped",
	"nr_anon_transparent_hugepages",
	"nr_vmscan_write",
	"nr_vmscan_immediate_reclaim",
	"nr_dirtied",
	"nr_written",

	"nr_kernel_misc_reclaimable",
	"nr_foll_pin_acquired",
	"nr_foll_pin_released",
	"nr_kernel_stack",
	"nr_page_table_pages",
	"nr_swapcached",

	# enum writeback_stat_item counters 
	"nr_dirty_threshold",
	"nr_dirty_background_threshold",

	# enum vm_event_item counters 
	"pgpgin",                           #从启动到现在读入的内存页数(从硬盘上读取到物理内存)
	"pgpgout",                          #从启动到现在把数据从物理内存写到磁盘的数据量
	"pswpin",                           #从启动到现在读入的就按分区页数
	"pswpout",
	"pgalloc_dma",
	"pgalloc_dma32",
	"pgalloc_normal", 
	"pgalloc_movable",
	"allocstall_dma",
	"allocstall_dma32",
	"allocstall_normal",
	"allocstall_movable",
	"pgskip_dma",
	"pgskip_dma32",
	"pgskip_normal",
	"pgskip_movable",

	"pgfree",                           #从启动到现在释放的页数
	"pgactivate",                       #从启动到现在激活的页数/移入活跃lru链表的page个数
	"pgdeactivate",                     #被移入非活跃lru链表的page个数
	"pglazyfree",

	"pgfault",                          #从启动到现在二级页面的错误数
	"pgmajfault",                       #从启动到现在一级页面错误数
	"pglazyfreed",                      #major page fault次数。却也分配内存pge时，若涉及io，即统计到pgmajfault,比如文件映射、swap in时，需要读写磁盘文件.

	"pgrefill",
	"pgreuse",
	"pgsteal_kswapd",
	"pgsteal_direct",
	"pgscan_kswapd",
	"pgscan_direct",
	"pgscan_direct_throttle",
	"pgscan_anon",
	"pgscan_file",
	"pgsteal_anon",
	"pgsteal_file",

	"zone_reclaim_failed",
	"pginodesteal",
	"slabs_scanned",
	"kswapd_inodesteal",
	"kswapd_low_wmark_hit_quickly",
	"kswapd_high_wmark_hit_quickly",
	"pageoutrun",

	"pgrotated",

	"drop_pagecache",
	"drop_slab",
	"oom_kill",

	"numa_pte_updates",
	"numa_huge_pte_updates",
	"numa_hint_faults",
	"numa_hint_faults_local",
	"numa_pages_migrated",

	"pgmigrate_success",
	"pgmigrate_fail",
	"thp_migration_success",
	"thp_migration_fail",
	"thp_migration_split",

	"compact_migrate_scanned",
	"compact_free_scanned",
	"compact_isolated",
	"compact_stall",
	"compact_fail",
	"compact_success",
	"compact_daemon_wake",
	"compact_daemon_migrate_scanned",
	"compact_daemon_free_scanned",

	"htlb_buddy_alloc_success",             #分配大页成功的次数
	"htlb_buddy_alloc_fail",                #失败的次数

	"unevictable_pgs_culled",
	"unevictable_pgs_scanned",
	"unevictable_pgs_rescued",
	"unevictable_pgs_mlocked",
	"unevictable_pgs_munlocked",
	"unevictable_pgs_cleared",
	"unevictable_pgs_stranded",

	"thp_fault_alloc",
	"thp_fault_fallback",
	"thp_fault_fallback_charge",
	"thp_collapse_alloc",
	"thp_collapse_alloc_failed",
	"thp_file_alloc",
	"thp_file_fallback",
	"thp_file_fallback_charge",
	"thp_file_mapped",
	"thp_split_page",
	"thp_split_page_failed",
	"thp_deferred_split_page",
	"thp_split_pmd",

	"thp_split_pud",
	"thp_zero_page_alloc",
	"thp_zero_page_alloc_failed",
	"thp_swpout",
	"thp_swpout_fallback",

	"balloon_inflate",
	"balloon_deflate",
	"balloon_migrate",

	"swap_ra",
	"swap_ra_hit",

	"direct_map_level2_splits",
	"direct_map_level3_splits",
	"nr_unstable" ]



b = BPF(text = bpf_text)
b.attach_kprobe(event = "vmstat_show", fn_name = "allpage")
table_vmstat = b.get_table("vmstat")

print("vmstat_text\t\t\t\tnumber")
while(1):
    for i in range (0, 150):
        for k, v in table_vmstat.items():
            if (i == k.value):
                print("%-25s%20lu"%(name[k.value], v.value))
    sleep(2)