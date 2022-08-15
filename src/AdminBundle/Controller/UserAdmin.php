<?php

namespace AdminBundle\Controller;

use Sonata\AdminBundle\Datagrid\ListMapper;
use Sonata\AdminBundle\Form\FormMapper;
use Sonata\AdminBundle\Route\RouteCollection;
use Sonata\UserBundle\Admin\Model\UserAdmin as BaseUserAdmin;
use Symfony\Component\HttpFoundation\RedirectResponse;
use Symfony\Component\Routing\Annotation\Route;


class UserAdmin extends BaseUserAdmin
{

    public function configureRoutes(RouteCollection $collection)
    {
        $collection->add('user_export', $this->getRouterIdParameter().'/csv_export');
    }

    /**
     * @inheritdoc
     */
    public function getFormBuilder()
    {
        $this->formOptions['data_class'] = $this->getClass();

        $options                      = $this->formOptions;
        $options['validation_groups'] = (!$this->getSubject() || is_null($this->getSubject()->getId())) ? 'CustomRegistration' : 'CustomProfile';

        $formBuilder = $this->getFormContractor()->getFormBuilder($this->getUniqid(), $options);

        $this->defineFormBuilder($formBuilder);

        return $formBuilder;
    }

    protected function configureListFields(ListMapper $listMapper): void
    {
        $listMapper
            ->addIdentifier('email')
            ->add('enabled', null, [
                'editable' => true,
            ])
            ->add('createdAt')
            ->add('getRoleName', null, [
                'label' => 'Role'
            ])
        ;
    }

    protected function configureFormFields(FormMapper $formMapper): void
    {
        // define group zoning
        $formMapper
            ->tab('User')
            ->with('Profile', ['class' => 'col-md-6'])->end()
            ->with('General', ['class' => 'col-md-6'])->end()
            ->end()
        ;

        $now = new \DateTime();

        $formMapper
            ->tab('User')
            ->with('General')
            ->add('email')
            ->add('plainPassword', 'text', [
                'required' => (!$this->getSubject() || is_null($this->getSubject()->getId())),
            ])
            ->add('enabled')
            ->add('receiveEmails')
            ->end()
            ->with('Profile')
            ->add('firstname', null, ['required' => false])
            ->add('lastname', null, ['required' => false])
            ->add('roles', 'choice', [
                'choices' => [
                    'ROLE_ADMIN'     => 'Admin',
                    'ROLE_MODERATOR' => 'Moderator',
                    'ROLE_USER'      => 'User',
                    'ROLE_TEACHER'   => 'Teacher',
                    'ROLE_STUDENT'   => 'Student',
                ],
                'expanded' => false,
                'multiple' => true,
                'required' => false,
            ])
            ->end()
            ->end()
        ;
    }

    public function userExportAction()
    {
        return new RedirectResponse($this->generateUrl('list'));
    }

}
