from django.db import migrations

SONGS = [
    (2, "Tum Se Hi", "mt9xg0mmt28", 30),
    (3, "Raataan Lambiyan", "gvyUuxdRdR4", 12),
    (4, "Kesariya", "BddP6PYo2gs", 50),
    (5, "Apna Bana Le", "ElZfdU54Cp8", 57),
    (6, "Tera Ban Jaunga", "Qdz5n1Xe5Qo", 30),
    (7, "Tum Hi Ho", "IJq0yyWug1k", 63),
    (8, "Kaise Hua", "WWXm39leYew", 63),
    (9, "Ve Maahi", "j6muwUGdvXw", 81),
    (10, "Tu Tu Hai Wahi", "H7aOCLPhuZo", 81),
    (11, "Agar Tum Saath Ho", "sK7riqg2mr4", 141),
    (12, "Humko Humise Chura Lo", "zWPsjhBaRb0", 70),
    (13, "Dil Diyan Gallan", "SAcpESN_Fk4", 40),
    (14, "Aankhon Mein Base Ho Tum", "h6xpqJT74BU", 50),
    (15, "Chand Sifarish", "zWEOx7TSM6I", 78),
    (16, "Gehra Hua", "0KYJPoGJcMc", 21),
    (17, "Rimjhim E Dhara Te", "Kfvdj8BVHuQ", 104),
    (18, "Tumi", "NQp3cbSkqbo", 61),
    (19, "Tumi Jake Bhalobasho", "LkUqqoKB4rM", 230),
    (20, "Tomake Chai", "JAP_Acr8jUM", 80),
    (21, "Purnota", "KmDLj7i06KY", 88),
    (22, "Rupkothar Jogote", "T8qMKs9Fjtg", 53),
    (23, "Dekhechhi Rupshagore", "ReBHEyAd2zk", 71),
    (24, "Beqarar Yeh Dil", "C0q7hl3n6c4", 116),
]


def seed(apps, schema_editor):
    Song = apps.get_model("book", "Song")
    for page, title, vid, start in SONGS:
        Song.objects.update_or_create(page=page, defaults={"title": title, "video_id": vid, "start_time": start})


def unseed(apps, schema_editor):
    apps.get_model("book", "Song").objects.filter(page__in=[s[0] for s in SONGS]).delete()


class Migration(migrations.Migration):
    dependencies = [("book", "0001_initial")]
    operations = [migrations.RunPython(seed, unseed)]
