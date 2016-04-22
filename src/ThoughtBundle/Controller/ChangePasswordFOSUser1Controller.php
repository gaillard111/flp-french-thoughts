<?php

namespace ThoughtBundle\Controller;

use FOS\UserBundle\Model\UserInterface;
use Symfony\Component\HttpFoundation\File\Exception\AccessDeniedException;
use Symfony\Component\HttpFoundation\RedirectResponse;
use Symfony\Component\HttpFoundation\Response;
use Sonata\UserBundle\Controller\ChangePasswordFOSUser1Controller as BaseController;
use Symfony\Component\Routing\Annotation\Route;

/**
 * Class ChangePasswordFOSUser1Controller
 * @package ThoughtBundle\Controller
 */
class ChangePasswordFOSUser1Controller extends BaseController
{
    /**
     * @return Response|RedirectResponse
     *
     * @throws AccessDeniedException
     *
     * @Route("/profile/change-password", name="user_change_password")
     */
    public function changePasswordAction()
    {
        $user = $this->getUser();

        if (!is_object($user) || !$user instanceof UserInterface) {
            $this->createAccessDeniedException('This user does not have access to this section.');
        }

        $form = $this->get('fos_user.change_password.form');
        $formHandler = $this->get('fos_user.change_password.form.handler');

        $process = $formHandler->process($user);

        if ($process) {
            $this->setFlash('fos_user_success', 'change_password.flash.success');

            return $this->redirect($this->getRedirectionUrl($user));
        }

        if (isset($_POST[$form->getName()]) and !$form->isValid()) {

            $errors = $this->getErrorMessages($form);

            $messages = $this->errorMessages($errors);

            $this->setFlash('sonata_user_error', $messages);

            return $this->redirect($this->generateUrl('sonata_user_profile_edit'));
        }

        return $this->render(
            'SonataUserBundle:ChangePassword:changePassword.html.'.$this->container->getParameter('fos_user.template.engine'),
            array('form' => $form->createView())
        );
    }

    /**
     * @param \Symfony\Component\Form\Form $form
     * @return string
     */
    private function getErrorMessages(\Symfony\Component\Form\Form $form)
    {
        $errors = array();

        foreach ($form->getErrors() as $key => $error) {
            if ($form->isRoot()) {
                $errors['#'][] = $error->getMessage();
            } else {
                $errors[] = $error->getMessage();
            }
        }

        foreach ($form->all() as $child) {
            if (!$child->isValid()) {
                $errors[$child->getName()] = $this->getErrorMessages($child);
            }
        }

        return $errors;
    }

    /**
     * @param $errors
     * @return string
     */
    private function errorMessages($errors)
    {
        $messages = '';

        foreach ($errors as $error) {
            if (!is_array($error)) {
                $messages .= "<li>$error</li>";
            } else {
                foreach ($error as $mess) {
                    if (!is_array($mess)) {
                        $messages .= "<li>$mess</li>";
                    } else {
                        foreach ($mess as $m) {
                            $messages .= "<li>$m</li>";
                        }
                    }
                }
            }
        }

        return $messages;
    }
}
