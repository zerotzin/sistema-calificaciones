from database import set_students_for_grade, get_students_by_grade

names_5to = [
    "Albino Romero Maria Ines",
    "Alferez Martinez Hector Arturo",
    "Angeles Araiza Santiago",
    "Avalos Duran Luciana",
    "Avendaño Nava Samantha",
    "Avila Martinez Ximena",
    "Bejar Garcia Saori Lucia",
    "Blanco Arreola Krishna Israel",
    "Bravo Ventura Angel Leonardo",
    "Camacho Sarmiento Santiago",
    "Carcamo Herrera Jonathan Alfonso",
    "Cardenas Romero Ciro Fabian",
    "Chaparro Cruz Yexalen",
    "Colin Cruz Elian Emiliano",
    "Cortes Aboytz Alonso",
    "Cruz Morales Josue",
    "Garcia Rodriguez Esteban",
    "Garcia Segura Dulce Aitana",
    "Gomez Flores Thiago",
    "Gutierrez Alvarez Jose Maria",
    "Hernandez Gonzalez Mateo",
    "Lira Piña Mauricio",
    "Lopez Romero Frida Gisselle",
    "Lopez Santiago Joshua",
    "Martinez Hernandez Fernanda",
    "Mendoza Ramon Isabella",
    "Ordaz Luna Anna Sofia",
    "Perez Aguilar Camila",
    "San Juan Garcia Itzayana",
    "Sandoval Mendoza Paula Fernanda",
    "Segura Alvarez Alberto",
    "Vazquez Ubaldo Maria Jose",
    "Ventura Martinez Regina"
]

names_6to = [
    "Abramoff Marquez Maia",
    "Bermudez Castro Barbara",
    "Bustamante Gomez Arely Itzayana",
    "Cerón Cruz Valentina",
    "Dominguez Laurido Eliot Gabriel",
    "Flores Escamilla Joaquin Ramses",
    "Garay Ordaz Gabino Jacob",
    "Garcia Ochoa Emma Patricia",
    "Garcia Ramirez Victoria Helena",
    "Hernandez Cruz Mateo",
    "Herrera Sotelo Elisa Simone",
    "Ibarra Galvez Arella",
    "Jacobo Aguilera Abril",
    "Jurado Fuerte Danna Sherlyn",
    "López Ibañez Fatima Zury",
    "Lopez Magaña Megan Abril",
    "Luna Gomez Ian Mateo",
    "Martinez Garcia Angel",
    "Martinez Guzman Melissa",
    "Orea Vela Misael Alexander",
    "Ortiz Martinez Josue De Jesus",
    "Quevedo Castillo Leah Sophia",
    "Ramirez Mendoza Jose Matias",
    "Reynoso Juarez Arianna",
    "Salgado Olvera Eduardo",
    "Santiago Martinez Jose Diego",
    "Sojo Gonzalez Mateo",
    "Tellez Fajardo Ethan Gael",
    "Tellez Praxedis Arely Abigail",
    "Vite Garcia Alexandra Renata",
    "Vite Garcia Braulio Miguel",
    "Vite Garcia Gabriel Antonio"
]

set_students_for_grade("5", names_5to)
set_students_for_grade("6", names_6to)

students_4 = get_students_by_grade("4")
students_5 = get_students_by_grade("5")
students_6 = get_students_by_grade("6")

print(f"Resumen de base de datos:")
print(f"- 4° Grado: {len(students_4)} alumnos")
print(f"- 5° Grado: {len(students_5)} alumnos")
print(f"- 6° Grado: {len(students_6)} alumnos")
print(f"Total general: {len(students_4) + len(students_5) + len(students_6)} alumnos registrados.")
