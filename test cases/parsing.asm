	.data
lwtest:
	.word	0
	.word	88
swtest:
	.space	4
	.text
	la	$28,lwtest
	lw	$1,0($28)
	lw	$2,4($28)
	add	$3,$1,$2
	la	$29,swtest
	sw	$3,0($29)