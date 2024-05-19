"""
Auxiliary functions to be used internally by the pyFS2000 package
"""
import numpy as np
from scipy.spatial.transform import Rotation


# def try_int(value, default=0) -> int:
#     """
#     Convert 'value' to an integer
#     If conversion raises an execption, returns 'default'
#     """
#     try:
#         return int(value)
#     except (ValueError, TypeError):
#         return int(default)
#
#
# def try_float(value, default=0.0) -> float:
#     """
#     Convert 'value' to an float
#     If conversion raises an execption, returns 'default'
#     """
#     try:
#         return float(value)
#     except (ValueError, TypeError):
#         return float(default)
#
#
# def try_value(value, param_type=float, default=0.0):
#     """
#     Convert 'value' to a type specified by 'param_type'
#     If conversion raises an execption, returns 'default'
#     """
#     try:
#         return param_type(value)
#     except (ValueError, TypeError):
#         return param_type(default)


def int_or_default(value: str, default=0) -> int:
    """Return an integer if the string is not empty, or default otherwise"""
    return int(value) if value != '' else default


def float_or_default(value: str, default=0.0) -> float:
    """Return a real number if the string is not empty, or default otherwise"""
    return float(value) if value != '' else default


def str_or_blank(value: str, length=0) -> str:
    """Return a string with a specified length from value, or blank"""
    if value is None:
        return ' ' * length
    if len(value) < length:
        return value[:length]
    return value + ' ' * (length - len(value))


def type_or_default(value: str, _type=float, default=0.0):
    """
    Return the string "value" converted to a type "_type" if the string is not
    empty, or default otherwise"""
    return _type(value) if value != '' else default


def getattr_nest(__o, name_list):
    """Call the getattr function recursively on a list"""
    if len(name_list) == 1:
        return getattr(__o, name_list[0])
    return getattr_nest(getattr(__o, name_list[0]), name_list[1:])


def cartesian_to_cylindrical(vector):
    """
    Convert Cartesian vector coordinates to Cylindrical coordinates

    vector : array-like
        Array containing (x,y,z) cartesian coordinates

    returns:
        Array containing (r,theta,z) cylindrical coordinates where:
            r     = sqrt(x**2 + y**2)
            theta = arctan(y/x)
            z     = z
        OBS: theta is the angle in the X-Y plane, positive from X to Y
        OBS: theta in degress. Function rubust to work for x = 0
    """
    x, y, z = vector[0], vector[1], vector[2]
    r = np.sqrt(x ** 2 + y ** 2)
    theta = np.arctan2(y, x)
    v = vector.copy()
    v[0], v[1], v[2] = r, np.degrees(theta), z
    return v


def cylindrical_to_cartesian(vector):
    """
    Convert Cylindrical vector coordinates to Cartesian coordinates

    vector : array-like
        Array containing (r,theta,z) cylindrical coordinates
        OBS: theta is the angle in the X-Y plane, positive from X to Y
        OBS: theta in degress

    returns:
        Array containing (x,y,z) cartesian coordinates where:
            x = r*cos(theta)
            y = r*sin(theta)
            z = z
    """
    r, theta, z = vector[0], np.radians(vector[1]), vector[2]
    v = vector.copy()
    v[0] = r * np.cos(theta)
    v[1] = r * np.sin(theta)
    v[2] = z
    return v


def cartesian_to_spherical(vector):
    """
    Convert Cartesian vector coordinates to Spherical coordinates

    vector : array-like
        Array containing (x,y,z) cartesian coordinates

    returns:
        Array containing (r,theta1,theta2) spherical coordinates where:
            r      = sqrt(x**2 + y**2 + z**2)
            theta1 = arctan(y/x)
            theta2 = arctan(z/(x*cos(theta1)+y*sin(theta1)))
        OBS: theta1 is the angle of the projected point in the X-Y plane,
             positive from positive X-axis to positive Y-axis
        OBS: theta2 is the angle of the actual point from the X-Z plane,
             positive from the plane X-Z plane to positive Y-axis
        OBS: theta1 and theta2 in degress. Function rubust for arctangent calcs
    """
    x, y, z = vector[0], vector[1], vector[2]
    r = np.sqrt(x ** 2 + y ** 2 + z ** 2)
    theta1 = np.arctan2(y, x)
    theta2 = np.arctan2(z, x * np.cos(theta1) + y * np.sin(theta1))
    v = vector.copy()
    v[0], v[1], v[2] = r, np.degrees(theta1), np.degrees(theta2)
    return v


def spherical_to_cartesian(vector):
    """
    Convert Spherical vector coordinates to Cartesian coordinates

    vector : array-like
        Array containing (r,theta1,theta2) spherical coordinates
        OBS: theta1 is the angle of the projected point in the X-Y plane,
             positive from positive X-axis to positive Y-axis
        OBS: theta2 is the angle of the actual point from the X-Z plane,
             positive from the plane X-Z plane to positive Y-axis
        OBS: theta1 and theta2 in degress

    returns:
        Array containing (x,y,z) cartesian coordinates where:
            x = r*cos(theta2)*cos(theta1)
            y = r*cos(theta2)*sin(theta1)
            z = r*sin(theta2)
    """
    r, theta1, theta2 = vector[0], np.radians(vector[1]), np.radians(vector[2])
    v = vector.copy()
    v[0] = r * np.cos(theta2) * np.cos(theta1)
    v[1] = r * np.cos(theta2) * np.sin(theta1)
    v[2] = r * np.sin(theta2)
    return v


def cartesian_to_conical(vector, p1=0, p2=45):
    """
    Convert Cartesian vector coordinates to Conical coordinates

    vector : array-like
        Array containing (x,y,z) cartesian coordinates

    p1 : float
        Radius of cone at z = 0

    p2 : float
        Angle of cone generatrix raletive to Z-axis (half of the aperture)

    OBS: The conical surface axis is always the Z-axis.

    returns:
        Array containing (r,theta,z) conical coordinates where:
            r     = sqrt(x**2 + y**2)
            theta = arctan(y/x)
            z     = (r-P1) / tan(P2)
        OBS: theta is the angle in the X-Y plane, positive from X to Y
        OBS: theta in degrees

    OBS: A conical coordinate system defines a conical surface in a 3D space.
    Therefore, it is not capable of representing all points in space, but only
    the points that lie on the conical surface. It is up to the user to make
    sure that the point represented by 'vector' belongs to the conical surface,
    otherwise the result will be meaningless.
    """
    x, y, z = vector[0], vector[1], vector[2]
    r = np.sqrt(x ** 2 + y ** 2)
    theta = np.arctan2(y, x)
    z = (r - p1) / np.tan(np.radians(p2))
    v = vector.copy()
    v[0], v[1], v[2] = r, np.degrees(theta), z
    return v


def conical_to_cartesian(vector, p1=0, p2=45):
    """
    Convert Cartesian vector coordinates to Conical coordinates

    vector : array-like
        Array containing (r,theta,z) conical coordinates

    p1 : float
        Radius of cone at z = 0

    p2 : float
        Angle of cone generatrix raletive to Z-axis (half of the aperture)

    OBS: The conical surface axis is always the Z-axis.

    returns:
        Array containing (x,y,z) cartesian coordinates where:
            x = r*cos(theta)
            y = r*sin(theta)
            z = (r-P1) / tan(P2)
        OBS: theta is the angle in the X-Y plane, positive from X to Y
        OBS: theta in degrees

    OBS: A conical coordinate system defines a conical surface in a 3D space.
    Therefore, it is not capable of representing all points in space, but only
    the points that lie on the conical surface. In the case of the conical
    coordinates being input, the (r,theta) coordinates are converted to the X-Y
    plane cartesian coordinates and then projected to the cone surface, so the
    input (z) coordinate is irrelevant. The returned (z) coordinate will be
    calculated based on the cone definition parameters P1 and P2.
    """
    r, theta, z = vector[0] if not np.isclose(vector[0], 0.0) else p1, np.radians(vector[1]), vector[2]
    v = vector.copy()
    v[0] = r * np.cos(theta)
    v[1] = r * np.sin(theta)
    v[2] = (r - p1) / np.tan(np.radians(p2))
    return v


def calc_ijk(p1, p2, p3, rot):
    """
    Calculate the unitary vectors i,j,k given 3 points or 2 points and a
    rotation angle
    """
    # Calculate local-X
    i = p2 - p1
    # Check if points are coincident
    if np.isclose(np.linalg.norm(i), 0.0):
        # If coincident, get the global-X axis
        i = np.array([1, 0, 0], dtype=float)
    else:
        # If not, take the unitary vector in the same direction as p2-p1
        i /= np.linalg.norm(i)
    # Calculate local-Y and local-Z
    if p3 is not None:
        # If there is a reference point defined, point local-Y to p3
        j = p3 - p1
        if np.isclose(np.linalg.norm(np.cross(i, j)), 0.0):
            # If 'i x j' is a null vector, either j is parallel to i or norm of j is zero. In any case, use global-Y
            j = np.array([0, 1, 0], dtype=float)
        else:
            # If not, take the component of j that is perpendicular to i, make it unitary
            j = j - np.dot(j, i) * i
            j = j / np.linalg.norm(j)
        # Take k as the cross product ixj
        k = np.cross(i, j)
        # Calculate the rotation angle
        jref = calc_ijk(p1, p2, None, 0)[1]
        theta = np.arccos(np.dot(j, jref))
        jp = Rotation.from_rotvec(theta * i).apply(jref)
        jm = Rotation.from_rotvec(-theta * i).apply(jref)
        rot = np.degrees(theta) if np.linalg.norm(jp - j) < np.linalg.norm(jm - j) else -np.degrees(theta)
    else:
        # Use default local coordinate system
        if np.isclose(abs(i[1]), 1.0):
            # Element is vertical, point local-Z to global-Z
            k = np.array([0, 0, 1])
            k = k - np.dot(k, i) * i
            k = k / np.linalg.norm(k)
            j = np.cross(k, i)
        else:
            # Element is not vertical, point local-Y to global-Y
            j = np.array([0, 1, 0])
            j = j - np.dot(j, i) * i
            j = j / np.linalg.norm(j)
            k = np.cross(i, j)
        # Apply rotation
        r = Rotation.from_rotvec(i * np.radians(rot))
        j, k = r.apply(j), r.apply(k)
    return i, j, k, rot
