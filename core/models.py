from django.db import models

class IndiceCAC(models.Model):
    fecha = models.DateField(unique=True, verbose_name="Mes del Índice")
    costo_construccion = models.DecimalField(max_digits=12, decimal_places=2)
    materiales = models.DecimalField(max_digits=12, decimal_places=2)
    mano_obra = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        # Esto hace que en la base de datos siempre se ordenen del más nuevo al más viejo
        ordering = ['-fecha']
        verbose_name = "Índice CAC"
        verbose_name_plural = "Índices CAC"

    def __str__(self):
        return f"CAC {self.fecha.strftime('%m-%Y')}"