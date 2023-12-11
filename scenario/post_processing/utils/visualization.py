"""Visualization utils to create movie from VTK files."""
import os
import pathlib
import tempfile
from typing import List, Optional

import pyvista as pv
import moviepy.video.io.ImageSequenceClip as moviepy_io


def get_sorted_files(data_dir: str,
                     file_format: str = "name",
                     split_token: str = "_"):
    """Returns list of files sorted according to [file_key].

    Order a set of .format files of the form
    ['name_1.format', 'name_2.format',...,'name_10.format',
    ...,'name_n.format'].

    The default sorting methods for list, list.sort()
    or sorted(list), order 'name_10.format' before 'name_2.format',
    which is not representative of the time series.

    In this function we sort according to the number..
    """

    if not os.path.exists(data_dir):
        raise IOError(f"Directory '{data_dir}' does not exist.")

    # Get a list of the files in the data directory.
    files = os.scandir(data_dir)

    # The files have file_format extension.
    files = [
        file for file in files if pathlib.Path(file.path).suffix == file_format
    ]

    # Sort the files to be read according to [file_key].
    def get_alphanum_key(file):
        file_name = pathlib.Path(file.path).stem
        file_name_splits = file_name.split(split_token)
        file_key = file_name_splits[-1]
        return int(file_key)

    files = sorted(files, key=get_alphanum_key)

    return files


def create_movie_from_vtk(vtk_output_dir: str,
                          movie_path: str,
                          virtual_display: bool = True,
                          scalars: str = None,
                          scalar_limits: Optional[List[float]] = None,
                          camera=None,
                          color: str = "blue",
                          cmap: str = None,
                          fps: int = 10) -> None:
    """Creates movie from a series of vtk files.

    The order of the vtk file name determines the order with which they
    are rendered in the movie. For example, vtk file 'frame_001.vtk' will
    appear before 'frame_002.vtk'.

    Args:
        vtk_output_dir: Directory containing the vtk files.
        movie_path: Path to save the movie.
        virtual_display: Whether to use a virtual display to render
            the movie.
        scalar: Scalars used to “color” the mesh. Accepts a string name
            of an array that is present on the mesh or an array equal to
            the number of cells or the number of points in the mesh.
            Array should be sized as a single vector.
        scalar_bounds: Color bar range for scalars. Defaults to minimum
            and maximum of scalars array. Example: [-1, 2].
        objects: Object of pyvista.PolyData type describing the domain or
            an object inside.
        camera: Camera description must be one of the following:
          - List of three tuples describing the position, focal-point
          and view-up: [(2.0, 5.0, 13.0), (0.0, 0.0, 0.0), (-0.7, -0.5, 0.3)]
          - List with a view-vector: [-1.0, 2.0, -5.0]
          - A string with the plane orthogonal to the view direction: 'xy'.
          https://docs.pyvista.org/api/plotting/_autosummary/pyvista.CameraPosition.html
        color: Color of the points used to represent particles. Default: "blue".
        cmap: string with the name of the matplotlib colormap to use
            when mapping the scalars. See available Matplotlib colormaps.
        fps: Number of frames per second to use in the movie. Renders only a
            subset of the vtk files to create the movie. This is done for
            speed purposes.
            Default: 10.
    """
    if virtual_display:
        pv.start_xvfb()

    pv.global_theme.background = "white"
    vtk_files = get_sorted_files(vtk_output_dir, ".vtk")
    frames = []

    plt = pv.Plotter(off_screen=True)
    plt.camera_position = camera

    with tempfile.TemporaryDirectory() as tmp_dir:
        for index, frame_file in enumerate(vtk_files):
            if index % int(round(60 / fps)) == 0:
                frame_path = os.path.join(vtk_output_dir, frame_file)
                image_frame_path = os.path.join(
                    tmp_dir, "frame_" + str(index).zfill(5) + ".png")
                mesh = pv.read(frame_path)
                plt.add_mesh(mesh,
                             name="fluid_block_snapshot",
                             scalars=scalars,
                             clim=scalar_limits,
                             render_points_as_spheres=True,
                             color=color,
                             cmap=cmap)
                plt.screenshot(image_frame_path, return_img=False)
                frames.append(image_frame_path)
        plt.close()

        clip = moviepy_io.ImageSequenceClip(frames, fps=fps)
        clip.write_videofile(movie_path)