	.file	"hello.c"
	.section	.rodata
.LC0:
	.string	"Hello Ker! func1: x=%d\n"
	.text
	.globl	func1
	.type	func1, @function
func1:
	pushl	%ebp
	movl	%esp, %ebp
	subl	$40, %esp
	movl	8(%ebp), %eax
	movl	%eax, 4(%esp)
	movl	$.LC0, (%esp)
	call	printf
	movl	8(%ebp), %eax
	addl	$1, %eax
	movl	%eax, -12(%ebp)
	cmpl	$3, -12(%ebp)
	jne	.L2
	movl	$99, %eax
	jmp	.L3
.L2:
	movl	-12(%ebp), %eax
	movl	%eax, (%esp)
	call	func1
.L3:
	leave
	ret
	.size	func1, .-func1
	.section	.rodata
.LC1:
	.string	"Hello Ker! main: x=%d, y=%d\n"
	.text
	.globl	main
	.type	main, @function
main:
	pushl	%ebp
	movl	%esp, %ebp
	andl	$-16, %esp
	subl	$32, %esp
	movl	$0, 24(%esp)
	movl	24(%esp), %eax
	addl	$1, %eax
	movl	%eax, (%esp)
	call	func1
	movl	%eax, 28(%esp)
	movl	28(%esp), %eax
	movl	%eax, 8(%esp)
	movl	24(%esp), %eax
	movl	%eax, 4(%esp)
	movl	$.LC1, (%esp)
	call	printf
	movl	$0, %eax
	leave
	ret
	.size	main, .-main
	.ident	"GCC: (Ubuntu/Linaro 4.6.3-1ubuntu5) 4.6.3"
	.section	.note.GNU-stack,"",@progbits
