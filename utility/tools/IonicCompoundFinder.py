from data.utilities.generators.PhaseDiagramCompositionEntryGenerator import \
    PhaseDiagramCompositionEntryGenerator
from data.utilities.generators.PhaseDiagramCompositionEntryGenerator import \
    PhaseDiagramCompositionEntryGenerator


class IonicCompoundFinder:
    """
    Class to find nearby compositions from a given nominal composition that
    can be charge neutral. Works by finding all combinations of elements in
    the supplied composition that are within a certain distance of the target
    composition with less than a certain number of atoms per unit cell.
    Distance is computed as the L_1 distance of the composition vector.
    Example: Fe3Al and FeAl are 0.5 apart.
    """

    # Nominal composition.
    nominal_composition = None

    # Maximum acceptable distance from nominal composition.
    maximum_distance = 0.1

    # Maximum number of atoms in formula unit.
    max_formula_unit_size = 5

    def set_nominal_composition(self, entry):
        """
        Function to set the target composition of the ionic compound.
        :param entry: Desired nominal composition with element names and
        fractions as keys and values respectively.
        :return:
        """
        if len(entry.get_element_ids()) < 2:
            raise ValueError("Must be at least a binary compound.")
        self.nominal_composition = entry

    def set_maximum_distance(self, dist):
        """
        Function to set the allowed maximum distance from the target value.
        Note, the distance is computed as the L_1 norm of the composition
        vector assuming one of the elements is a balance (i.e., only sum the
        difference for N-1 elements).
        :param dist: Maximum allowed distance.
        :return:
        """
        self.maximum_distance = dist

    def set_max_formula_unit_size(self, size):
        """
        Function to set maximum number of atoms in formula unit. Example:
        NaCl has 2.
        :param size: Maximum allowed size.
        :return:
        """
        self.max_formula_unit_size = size

    def find_all_compounds(self, lookup_path):
        """
        Function to find all the compounds in the vicinity of the target
        composition.
        :param lookup_path: Path to the file containing the property values.
        :return: accepted: A list of Composition Entry's.
        """

        # Get elements in the nominal compound.
        elems = self.nominal_composition.get_element_ids()
        fracs = self.nominal_composition.get_element_fractions()

        # Get list of all possible compositions.
        gen = PhaseDiagramCompositionEntryGenerator()
        gen.set_elements_by_index(elems)
        gen.set_even_spacing(False)
        gen.set_order(1, len(elems))
        gen.set_size(self.max_formula_unit_size)
        all_possibilities = gen.generate_entries()

        hits = []
        # Find which ones fit the desired tolerance.
        for entry in all_possibilities:
            # See if it is close enough in composition.
            dist = 0.0
            for e in range(len(elems)):
                dist += abs(fracs[e] - entry.get_element_fraction(id=elems[e]))

            if dist > self.maximum_distance:
                continue

            # See if it is ionically neutral.
            ox_g = OxidationStateGuesser()
            en = LookUpData.load_property("Electronegativity",
                                          lookup_dir=lookup_path)
            os = LookUpData.load_special_property("OxidationStates",
                                                  lookup_dir=lookup_path)
            ox_g.set_electronegativity(en)
            ox_g.set_oxidationstates(os)
            can_form_ionic = len(ox_g.get_possible_states(entry)) > 0

            if can_form_ionic:
                hits.append((dist, entry))

        # Sort such that closest is first.
        hits.sort()

        # Get only compositions.
        accepted = [i[1] for i in hits]
        return accepted

if __name__ == "__main__":
    y = LookUpData()
    x = IonicCompoundFinder(y)
    entry = {"Sc":0.25,"Ti":0.25,"P":0.125,"Si":0.125,"C":0.125,"N":0.125}
    x.set_max_formula_unit_size(6)
    x.set_maximum_distance(6)
    x.set_nominal_composition(entry)
    z = x.find_all_compounds()
    # print z[250]