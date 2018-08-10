<?php

namespace Application\Sonata\UserBundle\Controller;

use Application\Sonata\UserBundle\Form\Type\ProfileInfoType;
use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Routing\Annotation\Route;
use Symfony\Component\Translation\Loader\ArrayLoader;
use Symfony\Component\Translation\Translator;

class ProfileFOSUser1Controller extends \Sonata\UserBundle\Controller\ProfileFOSUser1Controller
{
    /**
     * @Route("/profile-info", name="sonata_user_edit_profile_info")
     * @param Request $request
     * @return Response
     * @throws \Doctrine\ORM\OptimisticLockException
     */
    public function editProfileInfoAction(Request $request)
    {
        $user = $this->getUser();

        $form = $this->createForm(new ProfileInfoType(), $user);
        $form->handleRequest($request);
        if ($form->isSubmitted()) {

            if ($form->isValid()) {

                $entityManager = $this->container->get('doctrine.orm.entity_manager');
                $entityManager->persist($user);
                $entityManager->flush();

            } else {

                $errors = $this->getErrorMessages($form);
                $messages = $this->errorMessages($errors);
                $this->setFlash('sonata_user_error', $messages);
            }
            return $this->redirectToRoute('sonata_user_profile_edit');
        }
        return $this->render('@ApplicationSonataUser/Profile/Form/edit_profile_info.html.twig', [
            'form'  => $form->createView(),
        ]);
    }

    /**
     * @param \Symfony\Component\Form\Form $form
     * @return array
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

            $error = $this->get('translator')->trans($error[0], [], 'SonataUserBundle');

            if   (!is_array($error)) {
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
