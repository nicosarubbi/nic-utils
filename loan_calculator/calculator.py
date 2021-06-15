import numpy
from collections import namedtuple
from .overwriters import alias, setargs


"""
Magic maths
    K: Capital
    Kd: Disbursabel Capital
    c: installment amount
    itax: TAX over interest
    etax: TAX over expenses
    a, A: administrative expenses (rate and minimum)
    b, B, F: notary expenses (rate, minimum, and fixed)
#######################################################
    Ka = A / a  # inflexion point where (a*K > A then A=0 else a=0)
    Kb = B / b  # inflexion point where (b*K > B then B=0 else b=0)
    i = 1.21    # plus IVA
    Kd = K - a K i + A i + b K + B + F       # how to find Kd with K
    K = (Kd + i A + B + F) / (1 - i a - ib)  # how to find K with Kd
"""


Installment = namedtuple('Installment',
    'month, amount, interest, capital, life, fire, serv, remaining_capital, ' +
    'itax, ftax, stax, tax')


class FrenchCalculator():
    code = 'FR'

    def first_payment(self, k, n, tna, exp, p):
        "returns the first payment in french amortization"
        t = tna / 12
        z = (1 - (1 / (1 + t)) ** n) / t                        # magic number
        base = k / z
        ix = k * t                                              # interest this payment
        kx = base - ix                                          # capital this payment
        lifex = k * exp.life                                    # life insurance this payment
        firex = k * exp.fire + exp.sivr * p                     # fire insurance this payment
        tax = (firex + exp.serv) * exp.etax + ix * exp.itax     # taxes
        payment = kx + ix + lifex + firex + exp.serv + tax      # total payment amount
        return payment

    def repayment_plan(self, k, n, tna, exp, p):
        "calculates the payment plan for french depreciation"
        t = tna / 12
        z = (1 - (1 / (1 + t)) ** n) / t    # magic number
        base = k / z                        # base payment

        installments = []
        rk = k                              # remaining capital
        for j in range(1, n + 1):
            ii = rk * t                             # interest this payment
            ki = base - ii                          # capital this payment
            life = rk * exp.life                    # life insurance this payment
            fire = rk * exp.fire + exp.sivr * p     # fire insurance this payment
            tax = ii * exp.itax + (fire + exp.serv) * exp.etax
            rk = rk - ki                            # remainint capital
            installment = Installment(
                month=j,
                amount=ki + ii + life + fire + exp.serv + tax,
                interest=ii,
                capital=ki,
                life=life,
                fire=fire,
                serv=exp.serv,
                remaining_capital=rk,
                itax=ii * exp.itax,
                ftax=fire * exp.etax,
                stax=exp.serv * exp.etax,
                tax=tax,
            )
            installments.append(installment)
        assert round(rk, 1) == 0
        return installments

    def max_capital(self, c, n, tna, exp, p, ltv=None):
        """ (p1 --> K) maximize the capital given a monthly payment amount
        c: maximum monthly payment
        p: collateral value
        """
        t = tna / 12
        etax = exp.etax + 1
        if p is not None:
            g = p * exp.sivr * etax + exp.serv * etax       # additive expenses
            h = exp.life + exp.fire * etax + t * exp.itax   # coeficient of expenses
            z = (1 - (1 / (1 + t)) ** n) / t                # mmmm... its magic
            k = z * (c - g) / (1 + z * h)                   # max capital
        else:
            g = exp.serv * etax
            h = exp.life + exp.fire * etax + (exp.sivr * etax / ltv) + t * exp.itax
            z = (1 - (1 / (1 + t)) ** n) / t
            k = z * (c - g) / (1 + z * h)
        return k

    def disbursable_capital(self, k, exp):
        " (K --> Kd) given a capital, return the disbursable capital"
        # K - max(K*a,A) * otax + max(K*b, B)*ntax + Fa * otax + Fb * ntax
        return k - self.expenses(k, exp)

    def revert_capital(self, Kd, exp):
        "(Kd --> K) given a disbursable capital, return the total capital"
        ax, Ax, bx, Bx = exp.a, exp.A, exp.b, exp.B
        if exp.a:
            Kx = exp.A / exp.a
            Kdx = self.disbursable_capital(Kx, exp)
            if Kd <= Kdx:
                ax = 0
            else:
                Ax = 0
        if exp.b:
            Kx = exp.B / exp.b
            Kdx = self.disbursable_capital(Kx, exp)
            if Kd <= Kdx:
                bx = 0
            else:
                Bx = 0

        otax = exp.otax + 1
        ntax = exp.ntax + 1
        K = (Kd + Ax * otax + Bx * ntax + exp.Fa * otax + exp.Fb * ntax) / (1 - ax * otax - bx * ntax)
        return K

    def expenses(self, K, exp):
        otax = exp.otax + 1
        ntax = exp.ntax + 1
        return max(K * exp.a, exp.A) * otax + max(K * exp.b, exp.B) * ntax + exp.Fa * otax + exp.Fb * ntax


class AmericanCalculator(FrenchCalculator):
    code = 'AM'

    def first_payment(self, k, n, tna, exp, p):
        "returns the first payment in american amortization"
        t = tna / 12
        ix = k * t
        lifex = k * exp.life
        firex = k * exp.fire + exp.sivr * p
        tax = (firex + exp.serv) * exp.etax + ix * exp.itax
        return ix + lifex + firex + exp.serv + tax

    def repayment_plan(self, k, n, tna, exp, p):
        "calculates the payment plan for american depreciation"
        installments = []
        t = tna / 12
        ix = k * t
        lifex = k * exp.life
        firex = k * exp.fire + exp.sivr * p
        tax = (firex + exp.serv) * exp.etax + ix * exp.itax
        amount = ix + tax + lifex + firex + exp.serv
        for i in range(1, n):
            installment = Installment(
                month=i,
                amount=amount,
                interest=ix,
                capital=0.0,
                life=lifex,
                fire=firex,
                serv=exp.serv,
                remaining_capital=k,
                itax=ix * exp.itax,
                ftax=firex * exp.etax,
                stax=exp.serv * exp.etax,
                tax=tax,
            )
            installments.append(installment)

        installment = Installment(
            month=n,
            amount=k+ix,
            interest=ix,
            capital=k,
            life=lifex,
            fire=firex,
            serv=exp.serv,
            remaining_capital=0.0,
            itax=ix * tax,
            ftax=firex * exp.etax,
            stax=exp.serv * exp.etax,
            tax=tax,
        )
        installments.append(installment)
        return installments

    def max_capital(self, c, n, tna, exp, p, ltv=None):
        """ (p1 --> K) maximize the capital given a monthly payment amount (american depreciation)
        c: maximum monthly payment
        """
        t = tna / 12
        etax = exp.etax + 1
        g = p * exp.sivr * etax + exp.serv * etax   # additive expenses
        h = exp.life + exp.fire * exp.etax + t * exp.itax    # coeficient of expenses
        k = (c - g) / (t + h)
        return k


####### LOAN SIMULATION ###############

class Expense():
    TAX = 0.21

    def __init__(self, **args):
        # over capital
        self.origination_pct = 0
        self.origination_min = 0
        self.origination_fixed = 0
        self.otax = self.TAX    # over origination
        self.notary_pct = 0
        self.notary_min = 0
        self.notary_fixed = 0
        self.ntax = 0           # over Notary

        # over payment
        self.life = 0
        self.fire = 0
        self.sivr = 0
        self.serv = 0
        self.itax = self.TAX    # over interest
        self.etax = self.TAX    # over ensurance and servicing

        setargs(self, **args)

    a = alias('origination_pct')
    A = alias('origination_min')
    Fa = alias('origination_fixed')
    b = alias('notary_pct')
    B = alias('notary_min')
    Fb = alias('notary_fixed')


class Product():
    CALCULATORS = {x.code: x() for x in [FrenchCalculator, AmericanCalculator]}

    def __init__(self, tna=0, collateral=0, depreciation='FR', **args):
        self.tna = tna
        self.collateral = collateral
        self.expenses = Expense(**args)
        self.depreciation = depreciation

    exp = alias('expenses')

    @property
    def calculator(self):
        return self.CALCULATORS[self.depreciation]

    def first_payment(self, k, n):
        return self.calculator.first_payment(k, n, self.tna, self.exp, self.collateral)

    def repayment_plan(self, k, n):
        return self.calculator.repayment_plan(k, n, self.tna, self.exp, self.collateral)

    def max_capital(self, c, n, ltv=None):
        return self.calculator.max_capital(c, n, self.tna, self.exp, self.collateral, ltv)

    def disbursable_capital(self, k):
        return self.calculator.disbursable_capital(k, self.exp)

    def revert_capital(self, kd):
        return self.calculator.revert_capital(kd, self.exp)

    def total_expenses(self, k):
        return self.calculator.expenses(k, self.exp)

    def avg_payment(self, k=0, n=1, plan=None):
        plan = plan or self.repayment_plan(k, n)
        return round(sum(x.amount for x in plan) / len(plan), 3)

    def cft(self, k=0, n=1, kd=None, plan=None):
        plan = plan or self.repayment_plan(k, n)
        kd = kd or self.disbursable_capital(k)
        payments = [-x.amount for x in plan]
        aux = numpy.irr([kd] + payments)
        cft = ((1 + aux) ** 12) - 1
        cft = cft or 0.0
        return round(cft, 3)

    def calculate(self, k, n):
        exp = self.expenses
        plan = self.repayment_plan(k, n)
        ori = max(exp.origination_min, k * exp.origination_pct) + exp.origination_fixed
        nota = max(exp.notary_min, k * exp.notary_pct) + exp.notary_fixed
        kd = self.disbursable_capital(k)
        return Result(
            term=n,
            disbursable=kd,
            capital=k,
            first_payment=self.first_payment(k, n),
            avg_payment=self.avg_payment(plan=plan),
            cft=self.cft(kd=kd, plan=plan),
            origination=ori,
            otax=ori * exp.otax,
            notary=nota,
            ntax=nota * exp.ntax,
        )

    def calculate_from_disbursable(self, kd, n):
        k = self.revert_capital(kd)
        return self.calculate(k, n)


class Result():
    def __init__(self, **args):
        self.term = 1
        self.disbursable = 0
        self.capital = 0
        self.first_payment = 0
        self.avg_payment = 0
        self.cft = 0
        self.origination = 0
        self.otax = 0
        self.notary = 0
        self.ntax = 0
        setargs(self, **args)
