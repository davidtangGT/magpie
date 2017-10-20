import numpy as np
from numpy.linalg import norm
import math
from Vassal.AtomImage import AtomImage

class Cell:
    """
    Represents the volume enclosing a set of atoms. Could represent a crystal
    unit cell or the simulation cell from a molecular dynamics calculation.
    """

    # Vectors representing the sides of cell. Stored in the format:
    # a_x b_x c_x
    # a_y b_y c_y
    # a_z b_z c_z
    simulation_cell = None

    # Inverse of the simulation cell. Set during the set_basis function.
    inverse_cell = None

    # List of all atoms.
    atoms = None

    # Whether the walls of the cell are periodic.
    face_is_periodic = None

    # Names of each atom type.
    type_name = None

    # Lattice vectors.
    lattice_vectors = None

    # Reciprocal lattice vectors.
    recip_lattice_vectors = None

    def __init__(self):
        """
        Creates an empty structure a = b = c = 1, alpha = beta = gamma = 90,
        and periodic boundary conditions in all directions.
        """
        basis = np.identity(3, dtype=float)
        self.simulation_cell = np.matrix(np.identity(3, dtype=float))
        self.set_basis(basis=basis)
        self.face_is_periodic = np.array([True]*3)

    def __copy__(self):
        """
        Function to override the copy() method.
        :return: A new instance with the appropriate properties set.
        """

        x = Cell()
        x.atoms = []
        for atom in self.atoms:
            n_atom = atom.__copy__()
            n_atom.set_cell(x)
            x.atoms.append(n_atom)

        x.face_is_periodic = self.face_is_periodic.copy()
        x.inverse_cell = self.inverse_cell.copy()
        x.simulation_cell = self.simulation_cell.copy()
        x.lattice_vectors = self.lattice_vectors.copy()
        x.recip_lattice_vectors = self.recip_lattice_vectors.copy()
        x.type_name = list(self.type_name)
        return x


    def __eq__(self, other):
        """
        Function to override the check for equality with another object of
        the same class.
        :param other: Other object.
        :return: True if equal, else False.
        """

        if isinstance(other, Cell):
            # Check to see if number of atoms is the same.
            if (self.n_atoms() != other.n_atoms()):
                return False
            # Compare basis.
            diff = self.simulation_cell - other.simulation_cell
            if norm(diff, 1) > 1e-4:
                return False

            # Compare atoms.
            for atom1 in self.atoms:
                # See if any atom in other matches this one regardless of ID.
                found = False
                for atom2 in other.atoms:
                    if atom1.__eq__(atom2):
                        found = True
                        break
                if not found:
                    return False

            return True
        return False

    def set_basis(self, basis=None, lengths=None, angles=None):
        """
        Function to define the basis. Format:
        a_x b_x c_x
        a_y b_y c_y
        a_z b_z c_z
        :param basis: 2-D numpy array containing the new basis.
        :param lengths: List of lengths that define the basis.
        :param angles: List of angles that define the basis.
        :return:
        """

        c_basis = basis

        if c_basis is None and lengths is not None and angles is not None:
            # Check input.
            if len(lengths) != 3 and len(angles) != 3:
                raise ValueError("Expected 3 lengths and/or 3 angles.")

            # Convert angles to radians.
            angles_radians = []
            for i in range(3):
                if angles[i] < 0 or angles[i] > 180:
                    raise ValueError("Angles must be between 0 and 180. Angle #"
                                     " "+str(i)+" = "+str(angles[i]))
                angles_radians.append(math.radians(angles[i]))

            c_basis = self.compute_basis(lengths, angles_radians)

        if c_basis is None:
            raise ValueError("Either basis must be specified or the lengths "
                             "and angles.")
        # Check input.
        if c_basis.shape != (3, 3):
            raise ValueError("Expected 3x3 matrix.")

        # Store old basis.
        old_cell = self.simulation_cell.copy()
        self.simulation_cell = c_basis

        # Make sure it has positive volume.
        if self.volume() <= 0 or np.isnan(self.volume()):
            self.simulation_cell = old_cell
            raise ValueError("Provided basis has non-positive volume.")

        # Get the inverse.
        self.inverse_cell = np.matrix(self.simulation_cell).I.A

        # Update cartesian coordinates of each atom.
        if self.atoms:
            for atom in self.atoms:
                atom.update_cartesian_coordinates()

        # Precompute the lattice vectors.
        self.lattice_vectors = np.zeros((3, 3), dtype=float)
        self.recip_lattice_vectors = np.zeros((3, 3), dtype=float)

        for i in range(3):
            self.lattice_vectors[i, :] = self.simulation_cell[:, i]
            self.recip_lattice_vectors[i, :] = self.inverse_cell[:, i]

    def compute_basis(self, lengths, angles_radians):
        """
        Function to compute the basis given lengths and angles (in radians).
        The a lattice vectors will be aligned in x direction, and the be will
        be in the xy plane.
        :param lengths: Lengths of the lattice vectors.
        :param angles_radians: Lattice angles in radians.
        :return: One possible set of basis vectors. Format:
        a_x b_x c_x
        a_y b_y c_y
        a_z b_z c_z
        """

        # Convert lengths to basis.
        basis = np.zeros((3, 3), dtype=float)
        basis[0][0] = lengths[0]
        basis[0][1] = lengths[1] * math.cos(angles_radians[2])
        basis[0][2] = lengths[2] * math.cos(angles_radians[1])
        basis[1][1] = lengths[1] * math.sin(angles_radians[2])
        basis[1][2] = lengths[2] * (math.cos(angles_radians[0])
        - math.cos(angles_radians[1]) * math.cos(angles_radians[2]))/ \
        math.sin(angles_radians[2])


        v = math.sqrt(1 - math.cos(angles_radians[0]) * math.cos(
            angles_radians[0]) - math.cos(angles_radians[1]) * math.cos(
            angles_radians[1]) - math.cos(angles_radians[2]) * math.cos(
            angles_radians[2]) + 2 * math.cos(angles_radians[0]) * math.cos(
            angles_radians[1]) * math.cos(angles_radians[2]))
        basis[2][2] = lengths[2] * v / math.sin(angles_radians[2])
        return basis

    def add_atom(self, a):
        """
        Function to add atom to cell.
        :param a: Atom to be added.
        :return:
        """
        self.atoms.append(a)
        a.set_id(len(self.atoms) - 1)
        a.set_cell(self)
        self.type_name = [None] * a.get_type()

    def direction_is_periodic(self, index):
        """
        Function to return whether a certain direction has boundary
        conditions.
        :param index: Desired direction (0: x, 1: y, 2: z)
        :return: True if that direction has periodic boundary conditions,
        else False.
        """
        return self.face_is_periodic[index]

    def volume(self):
        """
        Function to compute the volume of the simulation cell.
        :return: Volume of the cell.
        """
        return self.simulation_cell[0][0] * (self.simulation_cell[1][1] *
                                             self.simulation_cell[2][2] -
                                             self.simulation_cell[2][1] *
                self.simulation_cell[1][2])- self.simulation_cell[0][1] * (
            self.simulation_cell[1][0] * self.simulation_cell[2][2] -
            self.simulation_cell[1][2] * self.simulation_cell[2][0]) + \
               self.simulation_cell[0][2] * (self.simulation_cell[1][0] *
                self.simulation_cell[2][1] - self.simulation_cell[1][1] *
                                             self.simulation_cell[2][0])

    def get_basis(self):
        """
        Function to get the basis of this structure.
        :return: A copy of the 2-D numpy array that defines the basis.
        """
        return self.simulation_cell.copy()

    def get_basis_matrix(self):
        """
        Function to get the basis of this structure.
        :return: A numpy matrix representing the basis.
        """
        return np.matrix(self.simulation_cell)

    def get_inverse_basis(self):
        """
        Function to get the inverse basis.
        :return: A copy of the 2-D numpy array that defines the inverse basis.
        """
        return self.inverse_cell.copy()

    def get_lattice_vectors(self):
        """
        Function to get the lattice vectors for this cell.
        :return: A 2-D numpy array where each row contains a lattice vector
        (0: a, 1: b, 2: c).
        """
        return self.lattice_vectors

    def get_lattice_parameters(self):
        """
        Function to get the lattice parameters.
        :return: A numpy array containing the lattice parameters.
        """
        output = [norm(self.simulation_cell[:, i]) for i in range(3)]
        return output

    def get_lattice_angles_radians(self, radians=True):
        """
        Function to get the angles between the lattice vectors.
        :return: Lattice angles in radians.
        """

        output_radians = []
        col0 = self.simulation_cell[:, 0]
        col1 = self.simulation_cell[:, 1]
        col2 = self.simulation_cell[:, 2]
        nc0 = norm(col0)
        nc1 = norm(col1)
        nc2 = norm(col2)

        # Compute cosines.
        output_radians.append(math.acos(np.dot(col1, col2)/ (nc1 * nc2)))
        output_radians.append(math.acos(np.dot(col2, col0) / (nc2 * nc0)))
        output_radians.append(math.acos(np.dot(col0, col1) / (nc0 * nc1)))
        if radians:
            return output_radians
        output_degrees = [math.degrees(output_radians[i]) for i in range(3)]
        return output_degrees

    def get_aligned_basis(self):
        """
        Function to get the basis vectors aligned such that a vector is
        parallel to the x-axis, and the b vector is in the x-y plane. Format:
        a_x b_x c_x
        a_y b_y c_y
        a_z b_z c_z
        :return: Aligned basis vectors as 2-D numpy array.
        """

        angles = self.get_lattice_angles_radians()
        lengths = self.get_lattice_parameters()
        return self.compute_basis(lengths, angles)

    def get_reciprocal_vectors(self):
        """
        Function to get the reciprocal lattice vectors for this cell. These
        are simply the matrix inverse of the lattice vectors.
        :return: A 2-D numpy array where each row contains a reciprocal
        vector (0: a, 1: b, 2: c).
        """
        return self.recip_lattice_vectors

    def get_atoms(self):
        """
        Function to get all atoms in the structure.
        :return: A list of all atoms.
        """
        return self.atoms

    def get_atom(self, index):
        """
        Function to get a single atom.
        :param index: Index of atom.
        :return: Atom at the desired index.
        """
        return self.atoms[index]

    def n_atoms(self):
        """
        Function to get the number of atoms in simulation cell.
        :return: Number of atoms.
        """
        return len(self.atoms)

    def n_types(self):
        """
        Function to get the number of atom types.
        :return: Number of atom types.
        """
        return len(self.type_name)

    def number_of_type(self, type):
        """
        Function to get the number of atoms of a certain type.
        :param type: Type index.
        :return: Number of atoms.
        """
        count = 0
        for atom in self.atoms:
            if atom.get_type() == type:
                count += 1

        return count

    def add_type(self, name=None):
        """
        Function to add a new atom type to this cell.
        :param name: Name of type (can be None)
        :return:
        """
        self.type_name.append(name)

    def set_type_name(self, index, name):
        """
        Function to define the name for an atom type. Note that indexing
        starts at 0.
        :param index: Index of atom type.
        :param name: Desired name.
        :return:
        """
        self.type_name[index] = name

    def replace_type_names(self, changes):
        """
        Function to change the names of several types at once.
        :param changes: Dictionary containing the changes to be made. Key:
        Current Name, Value: New Name
        :return:
        """

        # Get the type ids corresponding to each name.
        name_map = {}
        for name in changes:
            name_map[name] = []

        for id, name in enumerate(self.type_name):
            for by_name in name_map:
                if by_name == name:
                    name_map[name].append(id)

        # Make the replacements.
        for by_name in name_map:
            new_name = changes[by_name]
            if not new_name:
                continue
            for id in name_map[by_name]:
                self.type_name[id] = new_name

    def merge_like_types(self):
        """
        Function to combine types that have the same name.
        :return:
        """

        cur_type = 0
        while cur_type < self.n_types():
            cur_name = self.get_type_name(cur_type)
            if cur_name is None:
                # Skip if name is None.
                cur_type += 1
                continue

            # Look to see if there is a duplicate name.
            matched_type = -1
            for t in range(self.n_types()):
                if t == cur_type:
                    continue
                name = self.get_type_name(t)
                if name is None:
                    continue
                if name == cur_name:
                    matched_type = t
                    break

            # If not matched, increment and move on.
            if matched_type == -1:
                cur_type += 1
                continue

            # Merge (matched_type -> cur_type) (a -> matched_type -> a-1)
            self.type_name.remove(self.type_name[matched_type])
            for atom in self.atoms:
                type = atom.get_type()
                if type == matched_type:
                    atom.set_type(cur_type)
                elif type > matched_type:
                    atom.set_type(type - 1)

    def set_type_radius(self, index, radius):
        """
        Function to set the radius of all atoms of a certain type.
        :param index: Index of the desired type.
        :param radius: Desired radius value.
        :return:
        """

        self.atoms[index].set_radius(radius)

    def get_type_name(self, index):
        """
        Function to get name of atom type.
        :param index: Index of atom type.
        :return: Name of atom type if it exists, else index.
        """
        if index >= self.n_types():
            return str(index)
        name = self.type_name[index]
        return str(index) if name is None else name

    def convert_fractional_to_cartesian(self, x):
        """
        Function to convert fractional coordinates to Cartesian.
        :param x: Fractional coordinates.
        :return: Cartesian coordinates.
        """

        return np.matmul(x, self.simulation_cell)

    def convert_cartesian_to_fractional(self, x):
        """
        Function to convert Cartesian coordinates to fractional.
        :param x: Cartesian coordinates.
        :return: Fractional coordinates.
        """

        return np.matmul(self.inverse_cell, x)

    def get_periodic_image(self, position, x, y, z):
        """
        Function to compute the position periodic image given its position in
        Cartesian coordinates.
        :param position: A list containing the Cartesian coordinates.
        :param x: Number of steps in the X direction.
        :param y: Number of steps in the Y direction.
        :param z: Number of steps in the Z direction.
        :return: New position.
        """

        output = list(position)
        l = [x, y, z]
        for i in range(3):
            output[i] += np.dot(l, self.simulation_cell[i, :])
        return output


    def get_minimum_distance(self, point1=None, point2=None, center=None,
                             neighbor=None):

        """
        Function to compute the minimum distance between any images of two
        points or to get the closest image of a neighboring atom to a given
        atom.

        Minimum distance algorithm:
        Compute the displacement between the points in Cartesian units.
        For each lattice vector:
            Compute the projection of the displacement onto this vector
            Divide that distance bvy the length of the lattice vector, and round
            to get the number of extra lattice vectors away this displacement
            vector is from the zero vector.
            Multiply the lattice vector by that factor and subtract the
            result from the current lattice vector to get a candidate
            displacement vector.
            If this vector is shorter than the current displacement vector,
            replace this vector with the new one.
        Compute the distance of this displacement vector.

        To get the closest image, we follow the exact same steps as computing
        the minimum distance. Except in the end, where we return the closest
        image.

        :param point1: Fractional coordinates of point1.
        :param point2: Fractional coordinates of point2.
        :param center: ID of central atom.
        :param neighbor: Neighboring atom.
        :return: Depending on the choice, either the minimum distance or the
        closest image.
        """

        disp = None
        subtract_pos = None
        flag = False
        image = None
        neighbor_atom = None

        if point1 is not None and point2 is not None:
            # Get the distance in cartesian units.
            disp = self.convert_fractional_to_cartesian(point2)
            subtract_pos = self.convert_cartesian_to_fractional(point1)
        elif center is not None and neighbor is not None:
            flag = True
            image = np.ones(3, dtype=int)
            center_atom = self.get_atom(center)
            neighbor_atom = self.get_atom(neighbor)
            # Compute the displacement vector between these atoms.
            disp = neighbor_atom.get_position_cartesian().copy()
            subtract_pos = center_atom.get_position_cartesian()


        for i in range(3):
            disp[i] -= subtract_pos[i]

        lat_vec = self.get_lattice_vectors()

        # For each direction, find the closest image.
        cur_dist = disp[0]**2 + disp[1]**2 + disp[2]**2
        for d in range(3):
            proj_D = disp[0] * lat_vec[d, 0] + disp[1] * lat_vec[d, 1] + disp[
                    2] * lat_vec[d, 2]
            proj_D /= lat_vec[d, 0]**2 + lat_vec[d, 1]**2 + lat_vec[d, 2]**2
            n_steps = int(round(proj_D))
            new_disp = list(disp)
            for i in range(3):
                new_disp[i] -= n_steps * lat_vec[d, i]
            new_dist = new_disp[0]**2 + new_disp[1]**2 + new_disp[2]**2
            if new_dist < cur_dist:
                if flag:
                    image[d] = -1 * n_steps
                disp = new_disp
                cur_dist = new_dist

        return math.sqrt(cur_dist) if not flag else AtomImage(neighbor_atom,
                                                              image)