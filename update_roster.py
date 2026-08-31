from database import set_students_for_grade, get_students_by_grade

names_4to = [
    "Abramoff Marquez Valentino",
    "Albor Martinez Daniela",
    "Almazán Cortes Ricardo Amauri",
    "Altamirano Ibañez Matias",
    "Benitez Salazar Ivanna",
    "Castillo Lozano Victoria Mabel",
    "Castro Guzman Emiliano",
    "Contreras Jimenez Luca",
    "Fernandez Bonifacio Constanza",
    "Fernandez Martínez Itzayana",
    "Garcia Piñon Romina",
    "Gomez Rivera Santiago",
    "Gutierrez Albor Matias",
    "Guzman Alcantar Benny Nathan",
    "Hernandez Lagunas Angel Ivan",
    "Hernandez Najera Maria Jose",
    "Juarez Alfaro Ian Caleb",
    "Lopez Hernandez Ileana Sofia",
    "Lopez Moreno Natalia Gisselle",
    "López Piña Jose Luis",
    "Martinez Lopez Samantha Valentina",
    "Martínez Pérez Leonardo Eden",
    "Munguia Martinez Hector Daniel",
    "Ochoa Rodriguez Maximo",
    "Perez Peña Ian Santiago",
    "Raygozo Enriquez Camila Rosario",
    "Reyes Sanchez Isaias Ariel",
    "Rios Martinez Regina",
    "Rodriguez Gonzalez Samara",
    "Rodriguez Uc Jesus Alejandro",
    "Sánchez Vivanco Marvin",
    "Segundo Primero Andrea Jacqueline"
]

set_students_for_grade("4", names_4to)

students = get_students_by_grade("4")
print(f"Exito: {len(students)} alumnos registrados para 4° Grado.")
for s in students:
    print(f"- {s['name']}")
