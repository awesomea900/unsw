.class public t9_whileloop
.super java/lang/Object
	
	
	; standard class static initializer 
.method static <clinit>()V
	
	
	; set limits used by this method
.limit locals 0
.limit stack 0
	return
.end method
	
	; standard constructor initializer 
.method public <init>()V
.limit stack 1
.limit locals 1
	aload_0
	invokespecial java/lang/Object/<init>()V
	return
.end method
.method public static main([Ljava/lang/String;)V
L0:
.var 0 is argv [Ljava/lang/String; from L0 to L1
.var 1 is vc$ Lt9_whileloop; from L0 to L1
	new t9_whileloop
	dup
	invokenonvirtual t9_whileloop/<init>()V
	astore_1
.var 2 is i I from L0 to L1
	iconst_0
	istore_2
L2:
	iload_2
	i2f
	ldc 100.5
	fcmpg
	iflt L4
	iconst_0
	goto L5
L4:
	iconst_1
L5:
	ifeq L3
L6:
	iload_2
	invokestatic VC/lang/System/putIntLn(I)V
	iload_2
	iconst_1
	iadd
	istore_2
L7:
	goto L2
L3:
	iload_2
	invokestatic VC/lang/System/putIntLn(I)V
L1:
	return
	
	; set limits used by this method
.limit locals 3
.limit stack 3
.end method
