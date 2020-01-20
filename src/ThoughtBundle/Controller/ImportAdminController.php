<?php

namespace ThoughtBundle\Controller;

use Sonata\AdminBundle\Controller\CoreController;
use Symfony\Component\HttpFoundation\File\UploadedFile;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;

/**
 * Class ImportAdminController
 *
 * @package ThoughtBundle\Controller
 */
class ImportAdminController extends CoreController
{
    /**
     * @param Request $request
     *
     * @return Response
     */
    public function importAdminPageAction(Request $request)
    {
        if ($request->getMethod() == 'POST') {
            if ($request->files->get('export_file')) {
                $upload = $request->files->get('export_file');

                if ($upload->getError()) {
                    $this->addFlash('sonata_user_error', $upload->getErrorMessage());
                } else {
                    $file = new UploadedFile($upload, 123, 'plain/text');

                    $parser = $this->container->get('thought.parser.service');

                    $result = $parser->parseFile($file);

                    $this->addFlash('sonata_user_success', $this->container->get('translator')->trans('sonata.admin.importPage.upload_success', ['%count%' => $result]));
                }
            } else {
                $this->addFlash('sonata_user_error', $this->container->get('translator')->trans('sonata.admin.importPage.not_suported'));
            }
        }

        return $this->render('@Thought/Sonata/Admin/importAdminPage.html.twig', [
            'base_template' => $this->getBaseTemplate(),
            'admin_pool'    => $this->container->get('sonata.admin.pool'),
            'blocks'        => $this->container->getParameter('sonata.admin.configuration.dashboard_blocks'),
        ]);
    }

    public function importAdminPageAuthorAction(Request $request)
    {
        if ($request->getMethod() == 'POST') {
            if ($request->files->get('export_file')) {
                $upload = $request->files->get('export_file');

                if ($upload->getError()) {
                    $this->addFlash('sonata_user_error', $upload->getErrorMessage());
                } else {
                    $file = new UploadedFile($upload, 123, 'plain/text');

                    $parser = $this->container->get('thought.parser.service');

                    $result = $parser->parseAuthorsFile($file);

                    $this->addFlash('sonata_user_success', $this->container->get('translator')->trans('sonata.admin.importPage.upload_success', ['%count%' => $result]));
                }
            } else {
                $this->addFlash('sonata_user_error', $this->container->get('translator')->trans('sonata.admin.importPage.not_suported'));
            }
        }

        return $this->render('@Thought/Sonata/Admin/importAuthorAdminPage.html.twig', [
            'base_template' => $this->getBaseTemplate(),
            'admin_pool'    => $this->container->get('sonata.admin.pool'),
            'blocks'        => $this->container->getParameter('sonata.admin.configuration.dashboard_blocks'),
        ]);
    }
}
