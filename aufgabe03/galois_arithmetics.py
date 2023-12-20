import copy

class Polynomial:

    GCM_IRREDUCIBLE = [0, 1, 2, 7, 128]
    _IRREDUCIBLE = GCM_IRREDUCIBLE
    poly_set = None
    poly_list = None

    def set_irreducible(self, irreducible: list):
        self._IRREDUCIBLE = irreducible

    @classmethod
    def from_bytes(cls, poly: bytes | bytearray):

        instance = cls()
        instance.poly_list = cls.block2poly(poly)

        return instance

    @classmethod
    def from_list(cls, poly: list):
        instance = cls()
        instance.poly_list = poly

        return instance
    
    @classmethod
    def from_set(cls, poly: set):
        instance = cls()
        instance.poly_set = poly

        return instance

    def to_bytes(self) -> bytes:
        return self.poly2block(self.to_list())
    
    def to_set(self) -> set:
        if self.poly_set == None:
            self.poly_set = set(self.poly_list)

        return self.poly_set

    def to_list(self) -> list:
        if self.poly_list == None:
            self.poly_list = list(self.poly_set)
        
        return self.poly_list

    @classmethod
    def zero(cls):
        return cls.from_list([])

    @staticmethod
    def clmul(a, b, irreducible) -> bytearray:
        return a * b

    def __xor__(self, x):
        return Polynomial.from_set((self.to_set() | x.to_set()) - (self.to_set() & x.to_set()))

    def __mul__(self, x):

        result = Polynomial.zero()

        for exponent in x.to_list():
            # Addition of the exponents is equivalent to multiplication
            a_multiplied = {self_exponent + exponent for self_exponent in self.to_list()}
            # The set operations are equivalent to XOR
            result ^= Polynomial.from_set(a_multiplied)

        return result % self._IRREDUCIBLE

    def __mod__(self, x):

        if len(x) == 0:
            raise ZeroDivisionError

        poly = copy.deepcopy(self)

        if len(poly.to_list()) == 0:
            return poly

        while (poly_max := max(poly.to_list())) >= (x_max := max(x)):
            shift_difference = poly_max - x_max

            shifted_irreducable = Polynomial.from_set({exp + shift_difference for exp in x})
            poly ^= shifted_irreducable

        return poly

    def __pow__(self, exp):

        if exp < 0:
            raise ValueError("Exponenet in pow may not be below 1")
        
        if exp == 0:
            return Polynomial.from_list([0])

        result = copy.deepcopy(self)
        # Square and multiply
        # Discard the first bit(exp-1) as this is "used" to set result to the initial value
        for bit_index in reversed(range(int.bit_length(exp)-1)):
            if (exp >> bit_index) & 1 == 1:
                result *= result
                result *= self
            else:
                result *= result
        
        return result

    def inverse(self):
        # Da es sich um eine endliche gruppe handelt(wenn man immer weiter mit sich selbst mutlipliziert kommt man irgendwann wieder bei sich selbst an)
        # ist self ** ((2**128)-1) == 1 und somit self**((2**128)-2)==das modulare inverse
        return self ** (2**max(self._IRREDUCIBLE)-2)

    @staticmethod
    def block2poly(block: bytes) -> list:
        # Keep in mind that this needs to be interpreted in the special GCM-like way
        output = []
        
        for byte_index, byte in enumerate(block):
            
            for bit_index in range(8):
                if (byte >> (7 - bit_index)) & 1 == 1:
                    output.append(byte_index * 8 + bit_index)

        return output

    @staticmethod
    def poly2block(poly: list) -> bytearray:
        
        # The length of the result will be minimum 16 byte, but can also be as long as it needs depending on the largest exponent
        output = bytearray(max(16, max(poly) // 8 + 1)) if len(poly) > 0 else bytearray(16)

        for bit in poly:
            current_byte = bit // 8
            output[current_byte] = output[current_byte] | (0b10000000 >> (bit % 8))

        return output

    def __deepcopy__(self, memo):
        return Polynomial.from_list(self.to_list().copy())
    
    def __ne__(self, other):
        if len((self ^ other).to_list()) != 0:
            return True
        else:
            return False

class CZPolynomial:

    @classmethod
    def from_poly_list(cls, coefficients: list):
        instance = cls()
        instance.coefficients = coefficients
        return instance

    @classmethod
    def from_bytes_list(cls, coefficients: list):
        instance = cls()
        instance.coefficients = [Polynomial.from_bytes(coefficient) for coefficient in coefficients]
        return instance

    @classmethod
    def zero(cls):
        return cls.from_poly_list([])

    def add_coefficients(self, new_elements: list):
        self.coefficients.extend([copy.deepcopy(element) for element in new_elements])

    def __add__(self, x):
        result = CZPolynomial.from_poly_list([coeff1 ^ coeff2 for coeff1, coeff2 in zip(self.coefficients, x.coefficients)])

        # zip only works as long as both are equally long: this accounts for the case where one is longer
        if len(self.coefficients) > len(x.coefficients):
            result.add_coefficients(self.coefficients[len(result.coefficients):])
        elif len(self.coefficients) < len(x.coefficients):
            result.add_coefficients(x.coefficients[len(result.coefficients):])
        
        # Remove highest exponents if they are zero
        for poly in reversed(result.coefficients):
            if poly.to_list() == []:
                result.coefficients = result.coefficients[:-1]
            else:
                break

            
        return result

    def __mul__(self, x):
        
        # Also keep in mind that index 0 is always the exponent 0 and so on
        result = CZPolynomial.zero()

        for exponent, x_coefficient in enumerate(x.coefficients):
            # First, multiply every element of x to every element of self
            coefficient_multiplied = [self_coefficient * x_coefficient for self_coefficient in self.coefficients]
            # Second, shift every element by its index because that will increment the exponent of H
            # This is realised by appending
            shifted_exponents = gen_empty_poly_list(exponent)
            shifted_exponents.extend(coefficient_multiplied)
            # Third, add this to the result
            result += CZPolynomial.from_poly_list(shifted_exponents)

        return result
    
    def __deepcopy__(self, memo):
        return CZPolynomial.from_poly_list([copy.deepcopy(coefficient) for coefficient in self.coefficients])

    def __pow__(self, exp, modulo=None):

        if exp < 0:
            raise ValueError("Exponenet in pow may not be below 0")
        
        if exp == 0:
            return CZPolynomial.from_poly_list([Polynomial.from_list([0])])
    
        result = copy.deepcopy(self)
        # Square and multiply
        # Discard the first bit(exp-1) as this is "used" to set result to the initial value
        for bit_index in reversed(range(int.bit_length(exp)-1)):
            if (exp >> bit_index) & 1 == 1:
                result *= result
                result *= self
            else:
                result *= result
            
            if modulo != None:
                result %= modulo
        
        return result
    
    def __divmod__(self, x):
        
        if len(x.coefficients) == 0:
            raise ZeroDivisionError

        # There will be this many elements in the result list, as the highest index must be stored which is calculated here
        divison_result = gen_empty_poly_list(len(self.coefficients) - len(x.coefficients) + 1)

        remainder = copy.deepcopy(self)
        divisor = copy.deepcopy(x)

        while (exponent_difference := len(remainder.coefficients) - len(divisor.coefficients)) >= 0:
            
            # Step 1: "shift" the exponents of the divisor to the left so that the highest exponents match
            shifted_polynomial = gen_empty_poly_list(exponent_difference)
            shifted_polynomial.extend(divisor.coefficients)

            # Step 2: Calculate this multiplication-factor, aka "mit was muss der koeffizient des höchsten divisorexponenten multipliziert werden, um den des 'dividenden'(oder wie man den auch immer nennt) zu matchen"
            # Also, da wir uns in galoisfeldern befinden: division = multiplikation mit dem inversen: muss ich von dem divisor das multiplikative inverse finden
            coefficient_multiplication_factor = remainder.coefficients[-1] * divisor.coefficients[-1].inverse()

            divison_result[exponent_difference] = coefficient_multiplication_factor

            # Step 3: Multiply all coefficients of the divisor by the coefficient_multiplication_factor
            coefficients_multiplied_and_shifted = CZPolynomial.from_poly_list([coefficient * coefficient_multiplication_factor for coefficient in shifted_polynomial])

            # Step 4: Subtract(the same as add) the remainder and the result of step 3: subtract all coefficients, which is the same as add, which is the same as XOR
            remainder += coefficients_multiplied_and_shifted


        return CZPolynomial.from_poly_list(divison_result), remainder
        
    def __floordiv__(self, x):
        return divmod(self, x)[0]
    
    def __mod__(self, x):
        return divmod(self, x)[1]
    
    def gcd(self, other):
        a = copy.deepcopy(self if len(self.coefficients) >= len(other.coefficients) else other)
        b = copy.deepcopy(other if len(self.coefficients) >= len(other.coefficients) else self)
        while b.coefficients != []:
            a, b = b, a % b

        return a.make_monisch()
    
    def make_monisch(self):
        highest_exponent_inverse = self.coefficients[-1].inverse()
        coefficients_monisch = [coefficient * highest_exponent_inverse for coefficient in self.coefficients]

        return CZPolynomial.from_poly_list(coefficients_monisch)
    
    def __int__(self):
        if self.coefficients == []:
            return 0
        
        # 1, if there is only one coefficient(for h**0) and it is 1(times x**0)
        if len(self.coefficients) == 1 and len(self.coefficients[0].to_list()) == 1 and 0 in self.coefficients[0].to_list():
            return 1
        
        return 5000
    
    def __ne__(self, other):

        if type(self) != type(other):
            return True

        if len(self.coefficients) != len(other.coefficients):
            return True
        
        for i in range(len(self.coefficients)):
            if self.coefficients[i] != other.coefficients[i]:
                return True
            
        return False


def gen_empty_poly_list(length: int):
    return [Polynomial.zero() for _ in range(length)]

def gcm_poly_add(a: list, b: list) -> list:

    a = CZPolynomial.from_bytes_list(a)
    b = CZPolynomial.from_bytes_list(b)

    return a + b

def gcm_poly_mul(a: list, b: list) -> list:

    a = CZPolynomial.from_bytes_list(a)
    b = CZPolynomial.from_bytes_list(b)

    return a * b

def gcm_poly_div(a: list, b: list) -> list:

    a = CZPolynomial.from_bytes_list(a)
    b = CZPolynomial.from_bytes_list(b)

    return a // b

def gcm_poly_gcd(a: list, b: list) -> list:

    a = CZPolynomial.from_bytes_list(a)
    b = CZPolynomial.from_bytes_list(b)
    
    return a.gcd(b)

def gcm_poly_mod(a: list, b: list) -> list:

    a = CZPolynomial.from_bytes_list(a)
    b = CZPolynomial.from_bytes_list(b)
    
    return a % b

def gcm_poly_pow(a: list, exp: int):

    a = CZPolynomial.from_bytes_list(a)

    return a ** exp

def gcm_poly_powmod(a: list, exp: int, modulo: list):
    a = CZPolynomial.from_bytes_list(a)
    modulo = CZPolynomial.from_bytes_list(modulo)

    return pow(a, exp, modulo)

if __name__ == "__main__":
    import base64
    a = CZPolynomial.from_poly_list([Polynomial.from_list([1,5,7,8,88]), Polynomial.from_list([0,5,7,18,51])])
    b = CZPolynomial.from_poly_list([Polynomial.from_list([1,5,6,8,19]), Polynomial.from_list([0,5,8])])

    # q = CZPolynomial.from_bytes_list([base64.b64decode(block) for block in ["E+qhgiymOJ9ttYkNlwm00w==","N04MTszz/j2EnWLfA1rK0Q==","d67NYqGx7zj4ZQttG3sVMg==", "gAAAAAAAAAAAAAAAAAAAAA=="]])
    q = CZPolynomial.from_bytes_list([base64.b64decode(block) for block in ["gAAAAAAAAAAAAAAAAAAAAA=="]])

    g = CZPolynomial.from_bytes_list([base64.b64decode(block) for block in ["qxipmd8xlNv1JcCz0yBU+Q==","W/dSR0GFQExxg+Y+UP4CBA==","8EMHqsEglMS1ohxNnLJLMw==", "PKqwlIPnFzM0cALo+jmxEQ=="]])
    p = CZPolynomial.from_bytes_list([base64.b64decode(block) for block in ["GwAbsyb8uopfXA/6KedvOQ==","AAAAAAAAAAAAAAAAAAAAAA==","7AYFUDpmpvjCIUeB0ad1NQ==", "ZGqzrSqg02ECPkyAxe0AlQ==", "gAAAAAAAAAAAAAAAAAAAAA=="]])
    c = g % q
    print(c)
    #[print(c1, c2) for c1, c2 in zip(["a", "b"], 1)]