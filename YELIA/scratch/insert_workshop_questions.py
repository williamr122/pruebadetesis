import json
from pathlib import Path

script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
content_path = project_root / "backend" / "content" / "course_content.json"

with content_path.open("r", encoding="utf-8-sig") as f:
    data = json.load(f)

# Define workshop questions for each unit
workshop_questions_by_unit = {
    1: [
        {
            "id": "u1-workshop-01",
            "unit_id": 1,
            "kind": "workshop",
            "number": 1,
            "topic": "Clases y Objetos",
            "level": "Basico",
            "question": "Observe el siguiente código:\n\nclass Estudiante {\n    private String nombre;\n    private int edad;\n    private String carrera;\n    private double promedio;\n\n    public String getNombre() { return nombre; }\n    public void setNombre(String nombre) { this.nombre = nombre; }\n    public int getEdad() { return edad; }\n    public void setEdad(int edad) { this.edad = edad; }\n    public String getCarrera() { return carrera; }\n    public void setCarrera(String carrera) { this.carrera = carrera; }\n    public double getPromedio() { return promedio; }\n    public void setPromedio(double promedio) { this.promedio = promedio; }\n\n    public void mostrarInformacion() {\n        System.out.println(nombre);\n        System.out.println(edad);\n        System.out.println(carrera);\n        System.out.println(promedio);\n    }\n}\n\n¿Cuál de las siguientes opciones completa correctamente el programa para crear tres objetos de tipo Estudiante y mostrar la información de cada uno?",
            "options": [
                "public class Main {\n    public static void main(String[] args) {\n        Estudiante e1 = new Estudiante();\n        e1.setNombre(\"Ana\");\n        e1.setEdad(20);\n        e1.setCarrera(\"Telemática\");\n        e1.setPromedio(9.1);\n        e1.mostrarInformacion();\n    }\n}",
                "public class Main {\n    public static void main(String[] args) {\n        Estudiante e1 = new Estudiante();\n        Estudiante e2 = new Estudiante();\n        Estudiante e3 = new Estudiante();\n\n        e1.setNombre(\"Ana\");\n        e1.setEdad(20);\n        e1.setCarrera(\"Telemática\");\n        e1.setPromedio(9.1);\n\n        e2.setNombre(\"Carlos\");\n        e2.setEdad(22);\n        e2.setCarrera(\"Sistemas\");\n        e2.setPromedio(8.7);\n\n        e3.setNombre(\"María\");\n        e3.setEdad(21);\n        e3.setCarrera(\"Software\");\n        e3.setPromedio(9.5);\n\n        e1.mostrarInformacion();\n        e2.mostrarInformacion();\n        e3.mostrarInformacion();\n    }\n}",
                "public class Main {\n    public static void main(String[] args) {\n        Estudiante e1 = new Estudiante();\n        Estudiante e2 = new Estudiante();\n        e1.mostrarInformacion();\n        e2.mostrarInformacion();\n    }\n}",
                "public class Main {\n    public static void main(String[] args) {\n        Estudiante e1 = new Estudiante();\n        Estudiante e2 = new Estudiante();\n        Estudiante e3 = new Estudiante();\n    }\n}"
            ],
            "answer": 1,
            "answer_letter": "B",
            "source": "UNIDAD 1 Introducción a la Programación Orientada a Objetos\\Taller Unidad 1\\workshop.pdf"
        }
    ],
    2: [
        {
            "id": "u2-workshop-01",
            "unit_id": 2,
            "kind": "workshop",
            "number": 1,
            "topic": "Herencia",
            "level": "Intermedio",
            "question": "Observe el siguiente código:\n\nabstract class Empleado {\n    String nombre;\n    double salario;\n    abstract void mostrarCargo();\n}\n\ninterface Trabajable {\n    void trabajar();\n}\n\nclass Docente extends Empleado implements Trabajable {\n    @Override\n    void mostrarCargo() {\n        System.out.println(\"Cargo: Docente\");\n    }\n\n    @Override\n    public void trabajar() {\n        System.out.println(\"El docente está impartiendo clases\");\n    }\n}\n\nclass Administrativo extends Empleado implements Trabajable {\n    @Override\n    void mostrarCargo() {\n        System.out.println(\"Cargo: Administrativo\");\n    }\n\n    @Override\n    public void trabajar() {\n        System.out.println(\"El administrativo está gestionando documentos\");\n    }\n}\n\n¿Cuál de las siguientes opciones completa correctamente el programa para crear un objeto Docente y un objeto Administrativo, ejecutando los métodos implementados en ambas clases?",
            "options": [
                "public class Main {\n    public static void main(String[] args) {\n        Docente docente = new Docente();\n        Administrativo administrativo = new Administrativo();\n        docente.mostrarCargo();\n        docente.trabajar();\n        administrativo.mostrarCargo();\n        administrativo.trabajar();\n    }\n}",
                "public class Main {\n    public static void main(String[] args) {\n        Docente docente = new Docente();\n        docente.mostrarCargo();\n    }\n}",
                "public class Main {\n    public static void main(String[] args) {\n        Administrativo administrativo = new Administrativo();\n        administrativo.trabajar();\n    }\n}",
                "public class Main {\n    public static void main(String[] args) {\n        Empleado empleado = new Empleado();\n        empleado.mostrarCargo();\n    }\n}"
            ],
            "answer": 0,
            "answer_letter": "A",
            "source": "UNIDAD 2 Lenguaje de Modelado Unificado\\Taller Unidad 2\\workshop.pdf"
        }
    ],
    3: [
        {
            "id": "u3-workshop-01",
            "unit_id": 3,
            "kind": "workshop",
            "number": 1,
            "topic": "Diagramas UML",
            "level": "Intermedio",
            "question": "Observe el siguiente código:\n\nclass Libro {\n    private String codigo;\n    private String titulo;\n    private String autor;\n\n    public Libro(String codigo, String titulo, String autor) {\n        this.codigo = codigo;\n        this.titulo = titulo;\n        this.autor = autor;\n    }\n\n    public void mostrarInformacion() {\n        System.out.println(\"Código: \" + codigo);\n        System.out.println(\"Título: \" + titulo);\n        System.out.println(\"Autor: \" + autor);\n    }\n}\n\n¿Cuál de las siguientes opciones completa correctamente el programa y permite mostrar la información del libro?",
            "options": [
                "public class Main {\n    public static void main(String[] args) {\n        Libro libro = new Libro(\n            \"L001\",\n            \"Programación Avanzada\",\n            \"Autor Ejemplo\"\n        );\n    }\n}",
                "public class Main {\n    public static void main(String[] args) {\n        Libro libro = null;\n        libro.mostrarInformacion();\n    }\n}",
                "public class Main {\n    public static void main(String[] args) {\n        Libro libro = new Libro(\n            \"L001\",\n            \"Programación Avanzada\",\n            \"Autor Ejemplo\"\n        );\n        System.out.println(\"Libro creado\");\n    }\n}",
                "public class Main {\n    public static void main(String[] args) {\n        Libro libro = new Libro(\n            \"L001\",\n            \"Programación Avanzada\",\n            \"Autor Ejemplo\"\n        );\n        libro.mostrarInformacion();\n    }\n}"
            ],
            "answer": 3,
            "answer_letter": "D",
            "source": "UNIDAD 3 Aplicación de la Programación Orientada a Objetos\\Taller Unidad 3\\workshop.pdf"
        }
    ],
    4: [
        {
            "id": "u4-workshop-01",
            "unit_id": 4,
            "kind": "workshop",
            "number": 1,
            "topic": "Acceso a archivos",
            "level": "Avanzado",
            "question": "Observe el siguiente código:\n\nclass Producto {\n    String codigo;\n    String nombre;\n    double precio;\n\n    void mostrarInformacion() {\n        System.out.println(\"Código: \" + codigo);\n        System.out.println(\"Nombre: \" + nombre);\n        System.out.println(\"Precio: \" + precio);\n    }\n}\n\n¿Cuál de las siguientes opciones completa correctamente el programa para crear cinco productos y mostrar la información de todos?",
            "options": [
                "public class Main {\n    public static void main(String[] args) {\n        Producto p1 = new Producto();\n        Producto p2 = new Producto();\n        Producto p3 = new Producto();\n        Producto p4 = new Producto();\n        Producto p5 = new Producto();\n\n        p1.codigo = \"P001\";\n        p1.nombre = \"Laptop\";\n        p1.precio = 850;\n\n        p2.codigo = \"P002\";\n        p2.nombre = \"Mouse\";\n        p2.precio = 20;\n\n        p3.codigo = \"P003\";\n        p3.nombre = \"Teclado\";\n        p3.precio = 35;\n\n        p4.codigo = \"P004\";\n        p4.nombre = \"Monitor\";\n        p4.precio = 180;\n\n        p5.codigo = \"P005\";\n        p5.nombre = \"Impresora\";\n        p5.precio = 120;\n\n        p1.mostrarInformacion();\n        p2.mostrarInformacion();\n        p3.mostrarInformacion();\n        p4.mostrarInformacion();\n        p5.mostrarInformacion();\n    }\n}",
                "public class Main {\n    public static void main(String[] args) {\n        Producto p1 = new Producto();\n        Producto p2 = new Producto();\n        Producto p3 = new Producto();\n\n        p1.codigo = \"P001\";\n        p1.nombre = \"Laptop\";\n        p1.precio = 850;\n\n        p2.codigo = \"P002\";\n        p2.nombre = \"Mouse\";\n        p2.precio = 20;\n\n        p3.codigo = \"P003\";\n        p3.nombre = \"Teclado\";\n        p3.precio = 35;\n\n        p1.mostrarInformacion();\n        p2.mostrarInformacion();\n        p3.mostrarInformacion();\n    }\n}",
                "public class Main {\n    public static void main(String[] args) {\n        Producto p1 = new Producto();\n        Producto p2 = new Producto();\n        Producto p3 = new Producto();\n        Producto p4 = new Producto();\n        Producto p5 = new Producto();\n\n        p1.codigo = \"P001\";\n        p1.nombre = \"Laptop\";\n        p1.precio = 850;\n\n        p2.codigo = \"P002\";\n        p2.nombre = \"Mouse\";\n        p2.precio = 20;\n\n        p3.codigo = \"P003\";\n        p3.nombre = \"Teclado\";\n        p3.precio = 35;\n\n        p4.codigo = \"P004\";\n        p4.nombre = \"Monitor\";\n        p4.precio = 180;\n\n        p5.codigo = \"P005\";\n        p5.nombre = \"Impresora\";\n        p5.precio = 120;\n    }\n}",
                "public class Main {\n    public static void main(String[] args) {\n        Producto p1 = new Producto();\n\n        p1.codigo = \"P001\";\n        p1.nombre = \"Laptop\";\n        p1.precio = 850;\n\n        p1.mostrarInformacion();\n    }\n}"
            ],
            "answer": 0,
            "answer_letter": "A",
            "source": "UNIDAD 4 Acceso a archivos y bases de datos\\Taller Unidad 4\\workshop.pdf"
        }
    ]
}

for unit in data.get("units", []):
    unit_id = unit.get("id")
    if unit_id in workshop_questions_by_unit:
        unit["workshop_questions"] = workshop_questions_by_unit[unit_id]
        print(f"Added workshop question to unit {unit_id}")

with content_path.open("w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)
print("Updated course_content.json with workshop questions successfully!")
