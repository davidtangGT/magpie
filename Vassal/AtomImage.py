import numpy as np
class AtomImage:
    """
    Class to uniquely identify an atom image. Key is atom ID, value is the
    periodic image.
    """

    # Pre-computed Cartesian coordinates of this image.
    position = None

    # Atom which this image is associated with.
    atom = None

    # Supercell in which this image is located.
    supercell = None

    def __init__(self, atom, image):
        """
        Constructor to create a new instance of the object.
        :param atom: Link to atom which is associated with this image.
        :param image: Supercell position (i.e., which image it is in)
        """

        self.supercell = image.copy()
        self.atom = atom
        self.compute_position()

    def __cmp__(self, other):
        """
        Function that acts as the comparator for AtomImage objects.
        :param other: Other AtomImage.
        :return: -1 is this < other, 0 if they are equal and +1 if this > other.
        """

        if self.atom.__eq__(other.atom):
            if self.supercell[0] != other.supercell[0]:
                return self.supercell[0] - other.supercell[0]
            elif self.supercell[1] != other.supercell[1]:
                return self.supercell[1] - other.supercell[1]
            else:
                return self.supercell[2] - other.supercell[2]
        else:
            return self.atom.get_id() - other.atom.get_id()

    def __eq__(self, other):
        """
        Function to override the check for equality with another object of
        the same class.
        :param other: Other object.
        :return: True if equal, else False.
        """

        if isinstance(other, AtomImage):
            return  self.atom.get_id == other.atom.get_id and np.array_equal(
                self.supercell, other.supercell)
        return False

    def __hash__(self):
        """
        Function to generate the hashcode for an object of this class.
        :return: Hashcode.
        """

        h = 7
        h = 43 * h + hash(self.atom)
        for e in self.supercell:
            h = 31 * h + (0 if e is None else hash(e))
        return h

    def compute_position(self):
        """
        Function to compute (or re-compute) position of this image.
        :return:
        """

        self.position = self.atom.get_cell().get_periodic_image(
            self.atom.get_position_cartesian(), self.supercell[0],
            self.supercell[1], self.supercell[2])

    def get_atom(self):
        """
        Function to get the atom at the center of this image.
        :return: Link to atom at the center.
        """

        return self.atom

    def get_atom_id(self):
        """
        Function to get the ID of the atom associated with this image.
        :return: ID number.
        """

        return self.atom.get_id()

    def get_supercell(self):
        """
        Function to get which supercell this image is located in.
        :return: Supercell coordinates.
        """

        return self.supercell.copy()

    def get_position(self):
        """
        Function to get the position (in Cartesian coordinates) of this image.
        :return: Position of atom.
        """

        return self.position

    def __str__(self):
        """
        Function to override the output format for the builtin print command.
        :return: Output string to be printed.
        """

        output = str(self.atom.get_id())
        image = self.get_supercell()

        if (image[0] == 0 and image[1] == 0 and image[2] == 0):
            return output

        output += "("
        for i in range(3):
            if image[i] != 0:
                output += "{0:d}{1:s}".format(image[i], str(chr(97+i)))
        output += ")"
        return output