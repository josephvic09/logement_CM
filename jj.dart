class etu {
  String? nom;
  String? matricule;
  List<double>? notes;

  etu(this.nom, this.matricule, this.notes);

  double moyenne() {
    if (notes == null || notes!.isEmpty) {
      return 0.0;
    }
    double sum = 0.0;
    for (var note in notes!) {
      sum += note;
    }
    return sum / notes!.length;
  }
  String mention() {
    double moy = moyenne();
    if (moy >= 16) {
      return "Très Bien";
    } else if (moy >= 14) {
      return "Bien";
    } else if (moy >= 12) {
      return "Assez Bien";
    } else if (moy >= 10) {
      return "Passable";
    } else {
      return "Insuffisant";
    }
  }


}
void main() {
  etu etudiant1 = etu("Alice", "2021001", [15.0, 18.0, 12.0]);
  print("Nom: ${etudiant1.nom}");
  print("Matricule: ${etudiant1.matricule}");
  print("Moyenne: ${etudiant1.moyenne()}");
  print("Mention: ${etudiant1.mention()}");
}