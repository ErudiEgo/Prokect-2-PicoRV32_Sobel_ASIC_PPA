OUTPUT_ARCH(riscv)
ENTRY(_start)
MEMORY { RAM (rwx) : ORIGIN = 0x00000000, LENGTH = 32K }
PHDRS { code PT_LOAD FLAGS(5); data PT_LOAD FLAGS(6); }
SECTIONS {
    .text : { KEEP(*(.text.start)) *(.text*) } > RAM :code
    .rodata : { *(.rodata*) *(.srodata*) } > RAM :code
    .data : { *(.data*) *(.sdata*) } > RAM :data
    PROVIDE(__global_pointer$ = . + 0x800);
    .bss (NOLOAD) : {
        . = ALIGN(4); __bss_start = .;
        *(.bss*) *(.sbss*) *(COMMON)
        . = ALIGN(4); __bss_end = .;
    } > RAM :data
    /DISCARD/ : { *(.comment) *(.eh_frame*) }
}
