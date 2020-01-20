<?php

namespace ThoughtBundle\Controller;

use Sonata\AdminBundle\Controller\CRUDController as Controller;
use Symfony\Component\HttpFoundation\RedirectResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpKernel\Exception\NotFoundHttpException;

/**
 * Class ThoughtAdminController
 *
 * @package ThoughtBundle\Controller
 */
class ThoughtAdminController extends Controller
{
    /**
     * @return RedirectResponse
     */
    public function publishAction()
    {
        $object = $this->admin->getSubject();

        if (!$object) {
            throw new NotFoundHttpException(sprintf('unable to find the object with id : %s', $object->getId()));
        }

        $publish = $object->getPublished() ? false : true;

        $object->setPublished($publish);

        $this->admin->update($object);

        $this->addFlash('sonata_flash_success', ($object->getPublished() ? 'Published' : 'Unpublished') . ' successfully');

        return new RedirectResponse($this->admin->generateUrl('list', $this->admin->getFilterParameters()));
    }

    /**
     * @param Request $request
     *
     * @return \Symfony\Component\HttpFoundation\Response
     */
    public function exportAction(Request $request)
    {
        $this->admin->checkAccess('export');

        $format = $request->get('format');

        if ($format != 'txt') {
            return parent::exportAction($request);
        }

        $allowedExportFormats = (array) $this->admin->getExportFormats();

        if (!in_array($format, $allowedExportFormats)) {
            throw new \RuntimeException(sprintf('Export in format `%s` is not allowed for class: `%s`. Allowed formats are: `%s`', $format, $this->admin->getClass(), implode(', ', $allowedExportFormats)));
        }

        $filters = $request->get('filter');

        $modelThought  = $this->container->get('thought.model.thought_model');
        $serviceExport = $this->container->get('thought.service.export');

        $thoughts = $modelThought->getFilteredThoughts($filters, $this->admin->getFilterFields());

        $response = $serviceExport->exportThoughts($thoughts);

        return $response;
    }
}
