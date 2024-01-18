from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterRasterDestination
from qgis.core import QgsProcessingParameterVectorDestination
import processing


class Mde_proceso(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer('MDEunido', 'MDE_unido', defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterDestination('Mde_relleno', 'MDE_relleno', createByDefault=True, defaultValue='G:/LiDAR_pruebas/NUEVO_INTENTO/MDE_relleno_huecos/MDE_unido/MDE_relleno.tif'))
        self.addParameter(QgsProcessingParameterRasterDestination('Mde_sin_depresiones', 'MDE_sin_depresiones', createByDefault=True, defaultValue='G:/LiDAR_pruebas/NUEVO_INTENTO/MDE_relleno_huecos/Fill/MDE_sin_huecos.tif'))
        self.addParameter(QgsProcessingParameterRasterDestination('Areas_problematicas', 'areas_problematicas', createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterDestination('Direccion_flujo_fill', 'direccion_flujo_fill', createByDefault=True, defaultValue='G:/LiDAR_pruebas/NUEVO_INTENTO/MDE_relleno_huecos/Fill/direccion_flujo_fill.tif'))
        self.addParameter(QgsProcessingParameterVectorDestination('Cuenca_vectorizado', 'cuenca_vectorizado', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue='G:/LiDAR_pruebas/NUEVO_INTENTO/MDE_relleno_huecos/cuencas/cuenca_vectorizado.shp'))
        self.addParameter(QgsProcessingParameterRasterDestination('Cuenca_raster', 'Cuenca_raster', createByDefault=True, defaultValue='G:/LiDAR_pruebas/NUEVO_INTENTO/MDE_relleno_huecos/cuencas/cuenca_raster.tif'))
        self.addParameter(QgsProcessingParameterRasterDestination('Celdas_acumulacion', 'celdas_acumulacion', optional=True, createByDefault=True, defaultValue='G:/LiDAR_pruebas/NUEVO_INTENTO/MDE_relleno_huecos/watershed/celdas_acumulacion.tif'))
        self.addParameter(QgsProcessingParameterRasterDestination('Direccion_drenaje_watershed', 'direccion_drenaje_watershed', optional=True, createByDefault=True, defaultValue='G:/LiDAR_pruebas/NUEVO_INTENTO/MDE_relleno_huecos/watershed/direccion_flujo_watershed.tif'))
        self.addParameter(QgsProcessingParameterRasterDestination('Etiqueta_cuenca_hidrograf', 'etiqueta_cuenca_hidrograf', optional=True, createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterDestination('Segmentos_transmision', 'segmentos_transmision', optional=True, createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterDestination('Semicuencas', 'semicuencas', optional=True, createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorDestination('Canales_drenaje', 'canales_drenaje', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterDestination('Conectividad_flujo', 'conectividad_flujo', createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterDestination('Cuencas_drenaje', 'cuencas_drenaje', createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorDestination('Cuencas_drenaje_vect', 'cuencas_drenaje_vect', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterDestination('Direccion_flujo_network', 'direccion_flujo_network', createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterDestination('Jerarquia_flujo', 'jerarquia_flujo', createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorDestination('Uniones_drenaje', 'uniones_drenaje', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(6, model_feedback)
        results = {}
        outputs = {}

        # Rellenar sin datos
        alg_params = {
            'BAND': 1,
            'DISTANCE': 2,
            'EXTRA': '',
            'INPUT': parameters['MDEunido'],
            'ITERATIONS': 1,
            'MASK_LAYER': None,
            'NO_MASK': False,
            'OPTIONS': '',
            'OUTPUT': parameters['Mde_relleno']
        }
        outputs['RellenarSinDatos'] = processing.run('gdal:fillnodata', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Mde_relleno'] = outputs['RellenarSinDatos']['OUTPUT']

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # r.fill.dir
        alg_params = {
            '-f': False,
            'GRASS_RASTER_FORMAT_META': '',
            'GRASS_RASTER_FORMAT_OPT': '',
            'GRASS_REGION_CELLSIZE_PARAMETER': 0,
            'GRASS_REGION_PARAMETER': None,
            'format': 0,
            'input': outputs['RellenarSinDatos']['OUTPUT'],
            'areas': parameters['Areas_problematicas'],
            'direction': parameters['Direccion_flujo_fill'],
            'output': parameters['Mde_sin_depresiones']
        }
        outputs['Rfilldir'] = processing.run('grass7:r.fill.dir', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Mde_sin_depresiones'] = outputs['Rfilldir']['output']
        results['Areas_problematicas'] = outputs['Rfilldir']['areas']
        results['Direccion_flujo_fill'] = outputs['Rfilldir']['direction']

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Channel network and drainage basins
        alg_params = {
            'DEM': outputs['Rfilldir']['output'],
            'THRESHOLD': 2,
            'BASIN': parameters['Cuencas_drenaje'],
            'BASINS': parameters['Cuencas_drenaje_vect'],
            'CONNECTION': parameters['Conectividad_flujo'],
            'DIRECTION': parameters['Direccion_flujo_network'],
            'NODES': parameters['Uniones_drenaje'],
            'ORDER': parameters['Jerarquia_flujo'],
            'SEGMENTS': parameters['Canales_drenaje']
        }
        outputs['ChannelNetworkAndDrainageBasins'] = processing.run('saga:channelnetworkanddrainagebasins', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Canales_drenaje'] = outputs['ChannelNetworkAndDrainageBasins']['SEGMENTS']
        results['Conectividad_flujo'] = outputs['ChannelNetworkAndDrainageBasins']['CONNECTION']
        results['Cuencas_drenaje'] = outputs['ChannelNetworkAndDrainageBasins']['BASIN']
        results['Cuencas_drenaje_vect'] = outputs['ChannelNetworkAndDrainageBasins']['BASINS']
        results['Direccion_flujo_network'] = outputs['ChannelNetworkAndDrainageBasins']['DIRECTION']
        results['Jerarquia_flujo'] = outputs['ChannelNetworkAndDrainageBasins']['ORDER']
        results['Uniones_drenaje'] = outputs['ChannelNetworkAndDrainageBasins']['NODES']

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # r.watershed
        alg_params = {
            '-4': False,
            '-a': False,
            '-b': False,
            '-m': False,
            '-s': True,
            'GRASS_RASTER_FORMAT_META': '',
            'GRASS_RASTER_FORMAT_OPT': '',
            'GRASS_REGION_CELLSIZE_PARAMETER': 0,
            'GRASS_REGION_PARAMETER': None,
            'blocking': None,
            'convergence': 5,
            'depression': None,
            'disturbed_land': None,
            'elevation': outputs['Rfilldir']['output'],
            'flow': None,
            'max_slope_length': None,
            'memory': 300,
            'threshold': 120,
            'accumulation': parameters['Celdas_acumulacion'],
            'basin': parameters['Etiqueta_cuenca_hidrograf'],
            'drainage': parameters['Direccion_drenaje_watershed'],
            'half_basin': parameters['Semicuencas'],
            'stream': parameters['Segmentos_transmision']
        }
        outputs['Rwatershed'] = processing.run('grass7:r.watershed', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Celdas_acumulacion'] = outputs['Rwatershed']['accumulation']
        results['Direccion_drenaje_watershed'] = outputs['Rwatershed']['drainage']
        results['Etiqueta_cuenca_hidrograf'] = outputs['Rwatershed']['basin']
        results['Segmentos_transmision'] = outputs['Rwatershed']['stream']
        results['Semicuencas'] = outputs['Rwatershed']['half_basin']

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # r.water.outlet
        alg_params = {
            'GRASS_RASTER_FORMAT_META': '',
            'GRASS_RASTER_FORMAT_OPT': '',
            'GRASS_REGION_CELLSIZE_PARAMETER': 0,
            'GRASS_REGION_PARAMETER': None,
            'coordinates': '348251.761376,4218000.279120',
            'input': outputs['Rwatershed']['drainage'],
            'output': parameters['Cuenca_raster']
        }
        outputs['Rwateroutlet'] = processing.run('grass7:r.water.outlet', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Cuenca_raster'] = outputs['Rwateroutlet']['output']

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # r.to.vect
        alg_params = {
            '-b': False,
            '-s': True,
            '-t': False,
            '-v': False,
            '-z': False,
            'GRASS_OUTPUT_TYPE_PARAMETER': 3,
            'GRASS_REGION_CELLSIZE_PARAMETER': 0,
            'GRASS_REGION_PARAMETER': None,
            'GRASS_VECTOR_DSCO': '',
            'GRASS_VECTOR_EXPORT_NOCAT': False,
            'GRASS_VECTOR_LCO': '',
            'column': 'value',
            'input': outputs['Rwateroutlet']['output'],
            'type': 2,
            'output': parameters['Cuenca_vectorizado']
        }
        outputs['Rtovect'] = processing.run('grass7:r.to.vect', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Cuenca_vectorizado'] = outputs['Rtovect']['output']
        return results

    def name(self):
        return 'MDE_proceso'

    def displayName(self):
        return 'MDE_proceso'

    def group(self):
        return 'MDE_hidrologia'

    def groupId(self):
        return 'MDE_hidrologia'

    def shortHelpString(self):
        return """<html><body><h2>Descripción del algoritmo</h2>
<p>Proceso para obtener la cuenca de flujos drenajes</p>
<h2>Parámetros de entrada</h2>
<h3>MDE_unido</h3>
<p></p>
<h3>MDE_relleno</h3>
<p></p>
<h3>MDE_sin_depresiones</h3>
<p></p>
<h3>areas_problematicas</h3>
<p></p>
<h3>direccion_flujo_fill</h3>
<p></p>
<h3>cuenca_vectorizado</h3>
<p></p>
<h3>Cuenca_raster</h3>
<p></p>
<h3>celdas_acumulacion</h3>
<p></p>
<h3>direccion_drenaje_watershed</h3>
<p></p>
<h3>etiqueta_cuenca_hidrograf</h3>
<p></p>
<h3>segmentos_transmision</h3>
<p></p>
<h3>semicuencas</h3>
<p></p>
<h3>canales_drenaje</h3>
<p></p>
<h3>conectividad_flujo</h3>
<p></p>
<h3>cuencas_drenaje</h3>
<p></p>
<h3>cuencas_drenaje_vect</h3>
<p></p>
<h3>direccion_flujo_network</h3>
<p></p>
<h3>jerarquia_flujo</h3>
<p></p>
<h3>uniones_drenaje</h3>
<p></p>
<h2>Salidas</h2>
<h3>MDE_relleno</h3>
<p></p>
<h3>MDE_sin_depresiones</h3>
<p></p>
<h3>areas_problematicas</h3>
<p></p>
<h3>direccion_flujo_fill</h3>
<p></p>
<h3>cuenca_vectorizado</h3>
<p></p>
<h3>Cuenca_raster</h3>
<p></p>
<h3>celdas_acumulacion</h3>
<p></p>
<h3>direccion_drenaje_watershed</h3>
<p></p>
<h3>etiqueta_cuenca_hidrograf</h3>
<p></p>
<h3>segmentos_transmision</h3>
<p></p>
<h3>semicuencas</h3>
<p></p>
<h3>canales_drenaje</h3>
<p></p>
<h3>conectividad_flujo</h3>
<p></p>
<h3>cuencas_drenaje</h3>
<p></p>
<h3>cuencas_drenaje_vect</h3>
<p></p>
<h3>direccion_flujo_network</h3>
<p></p>
<h3>jerarquia_flujo</h3>
<p></p>
<h3>uniones_drenaje</h3>
<p></p>
<br><p align="right">Autor del algoritmo: Antonio Miguel Gámiz Fuentes</p><p align="right">Versión del algoritmo: 1</p></body></html>"""

    def createInstance(self):
        return Mde_proceso()
