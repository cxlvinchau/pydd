from pydd.bdd import BDD

bdd = BDD()
x0 = bdd.create_variable_node("x0")
x0_prime = bdd.create_variable_node("x0", is_primed=True)
x1 = bdd.create_variable_node("x1")
x1_prime = bdd.create_variable_node("x1", is_primed=True)

# States
x00 = bdd.conjunction(bdd.neg(x0), bdd.neg(x1))
x01 = bdd.conjunction(bdd.neg(x0), x1)
x10 = bdd.conjunction(x0, bdd.neg(x1))
x11 = bdd.conjunction(x0, x1)

# Primed states
x00_prime = bdd.conjunction(bdd.neg(x0_prime), bdd.neg(x1_prime))
x01_prime = bdd.conjunction(bdd.neg(x0_prime), x1_prime)
x10_prime = bdd.conjunction(x0_prime, bdd.neg(x1_prime))
x11_prime = bdd.conjunction(x0_prime, x1_prime)

# Transitions
t0 = bdd.conjunction(x00, x01_prime)
t1 = bdd.conjunction(x01, x10_prime)
t2 = bdd.conjunction(x10, x11_prime)
t3 = bdd.conjunction(x11, x01_prime)
delta = bdd.disjunction(bdd.disjunction(t0, t1), bdd.disjunction(t2, t3))

pre = bdd.pre_image(delta, x10)

bdd.clear([delta, pre])
print(bdd.to_dot())
print(pre)