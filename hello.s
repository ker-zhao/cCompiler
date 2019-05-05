.section    .rodata
.LC1:
	.string "Hello Ker! func1: x=%d\n"
.LC4:
	.string "Hello Ker! main: x=%d, y=%d\n"
.data
.text
.globl  main
func1:
	
    pushl   %ebp
    movl    %esp, %ebp
    subl    $64, %esp
    pushl   %ecx
    pushl   %edx
    pushl   %ebx
    pushl   %esi
    pushl   %edi

	movl 8(%ebp), %eax
	pushl %eax
	movl %eax, 8(%ebp)
	pushl $.LC1
	call printf
	addl $8, %esp
	movl 8(%ebp), %eax
	addl $1, %eax
	movl %eax, %edi
	movl %edi, -4(%ebp)
	movl $6, -8(%ebp)
	movl -4(%ebp), %eax
	movl -8(%ebp), %ebx
	cmpl %ebx, %eax
	movl %eax, %esi
	jne .LC2
	movl $99, %eax
	
    popl    %edi
    popl    %esi
    popl    %ebx
    popl    %edx
    popl    %ecx
    addl   $64, %esp
    leave
    ret

	jmp .LC3
.LC2:
	movl -4(%ebp), %eax
	pushl %eax
	movl %eax, -4(%ebp)
	call func1
	addl $4, %esp
	movl %eax, %eax
	
    popl    %edi
    popl    %esi
    popl    %ebx
    popl    %edx
    popl    %ecx
    addl   $64, %esp
    leave
    ret

.LC3:
	movl $88, %eax
	
    popl    %edi
    popl    %esi
    popl    %ebx
    popl    %edx
    popl    %ecx
    addl   $64, %esp
    leave
    ret

	
    popl    %edi
    popl    %esi
    popl    %ebx
    popl    %edx
    popl    %ecx
    addl   $64, %esp
    leave
    ret

main:
	
    pushl   %ebp
    movl    %esp, %ebp
    subl    $64, %esp
    pushl   %ecx
    pushl   %edx
    pushl   %ebx
    pushl   %esi
    pushl   %edi

	movl $0, -4(%ebp)
	movl -4(%ebp), %eax
	pushl %eax
	movl %eax, -4(%ebp)
	call func1
	addl $4, %esp
	movl %eax, -8(%ebp)
	movl -8(%ebp), %eax
	pushl %eax
	movl %eax, -8(%ebp)
	movl -4(%ebp), %eax
	pushl %eax
	movl %eax, -4(%ebp)
	pushl $.LC4
	call printf
	addl $12, %esp
	movl $0, %eax
	
    popl    %edi
    popl    %esi
    popl    %ebx
    popl    %edx
    popl    %ecx
    addl   $64, %esp
    leave
    ret

	
    popl    %edi
    popl    %esi
    popl    %ebx
    popl    %edx
    popl    %ecx
    addl   $64, %esp
    leave
    ret

