<?php

namespace ThoughtBundle\Controller;

use Sonata\AdminBundle\Controller\CRUDController as Controller;
use Symfony\Component\HttpFoundation\RedirectResponse;
use Symfony\Component\HttpKernel\Exception\NotFoundHttpException;

/**
 * Class ThoughtAdminController
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

        $this->addFlash('sonata_flash_success', 'Published successfully');

        return new RedirectResponse($this->admin->generateUrl('list', $this->admin->getFilterParameters()));
    }
}
