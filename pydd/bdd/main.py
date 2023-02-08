from pydd.bdd.bdd import BDD

bdd = BDD()
n = bdd.get_one_node()

for i in range(400):
    x = bdd.create_variable_node(f"x{i}")
    n = bdd.conjunction(n, x)

print(n)
